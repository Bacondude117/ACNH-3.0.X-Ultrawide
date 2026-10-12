"""Background-copy regression checks. Game instructions remain external."""
import math
import struct

from build import require


def verify_capture_hook(config, patches):
    from verify import _machine, _registers
    from unicorn import arm64_const as r
    count = 0
    for base in (0, 0x7100000000):
        for aspect in (16/9, 43/18, 4/3, 32/9):
            for ortho in (False, True):
                for size in ((50, 640), (1920, 1080), (2580, 1080), (1920, 0)):
                    for flags in (0, 0x90000000):
                        u = _machine(patches, base)
                        draw = 0x200000
                        u.reg_write(r.UC_ARM64_REG_X21, draw)
                        u.mem_write(draw+0xc0,struct.pack('<Q',draw+0x100))
                        u.mem_write(draw+0x128,struct.pack('<2f',1920,1080))
                        for i in range(32):
                            u.reg_write(r.UC_ARM64_REG_Q0+i, (i+1)*0x123456789abcdef123456789)
                        for index, value in ((2,1920), (3,size[1]/1080), (8,size[1]), (9,size[0])):
                            u.reg_write(r.UC_ARM64_REG_S0+index, struct.unpack('<I',struct.pack('<f',value))[0])
                        for offset,value in ((0x10,2/aspect), (0x24,-2), (0x4c,int(ortho))):
                            u.mem_write(draw+offset,struct.pack('<f',value))
                        u.reg_write(r.UC_ARM64_REG_NZCV,flags)
                        before = _registers(u)
                        simd = [u.reg_read(r.UC_ARM64_REG_Q0+i) for i in range(32)]
                        site = base+0x3a2eabc
                        u.emu_start(site,site+4,count=80)
                        require(u.reg_read(r.UC_ARM64_REG_PC)==site+4,'Capture hook did not return')
                        require(_registers(u)==before,'Capture hook changed registers, stack or flags')
                        require(all(u.reg_read(r.UC_ARM64_REG_Q0+i)==simd[i] for i in range(32) if i!=2),'Capture hook changed scratch SIMD')
                        actual=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_ARM64_REG_S2)))[0]
                        expected=size[0]/(1920 if ortho else 1080*aspect)
                        require(math.isclose(actual,expected,rel_tol=2e-6),'Incorrect projected capture width')
                        count+=1
    return dict(executions=count,register_preservation='passed',orthographic_passthrough='passed',load_bases=2)


def verify_capture_coordinates(image, patches):
    """Execute the verified original 3.0.3 setup block with the new hook."""
    import unicorn as uc
    from unicorn import arm64_const as r
    count = 0
    for aspect in (16/9,43/18):
        for ortho in (False,True):
            for panel,side,width,height in ((-690,-265,50,640),(-690,265,50,640),(0,0,2580,1080),(-836,0,834,160)):
                for scale in (1,.8):
                    u=uc.Uc(uc.UC_ARCH_ARM64,uc.UC_MODE_ARM)
                    u.mem_map(0x3a2e000,0x1000)
                    u.mem_write(0x3a2e000,bytes(image[0x3a2e000:0x3a2f000]))
                    u.mem_map(0x3f06000,0x1000)
                    for p in patches:
                        if 0x3a2e000<=p['address']<0x3a2f000 or 0x3f06000<=p['address']<0x3f07000:
                            u.mem_write(p['address'],p['new'])
                    u.mem_map(0x100000,0x10000)
                    pane,parent,draw,reference,texture,context,sp=(0x101000,0x102000,0x103000,0x104000,0x105000,0x106000,0x108000)
                    u.mem_write(pane+0x30,struct.pack('<3f',side,0,0))
                    for off,value in ((0x70,scale),(0x84,scale),(0x7c,panel*scale),(0x8c,-6)):
                        u.mem_write(parent+off,struct.pack('<f',value))
                    for off,value in ((0x10,1/aspect),(0x24,1),(0x4c,int(ortho))):
                        u.mem_write(draw+off,struct.pack('<f',value))
                    u.mem_write(draw+0xc0,struct.pack('<Q',reference))
                    u.mem_write(reference+0x28,struct.pack('<2f',1920,1080))
                    for reg,value in ((r.UC_ARM64_REG_X23,pane),(r.UC_ARM64_REG_X22,parent),(r.UC_ARM64_REG_X21,draw),
                                      (r.UC_ARM64_REG_X19,texture),(r.UC_ARM64_REG_X26,context),(r.UC_ARM64_REG_SP,sp),(r.UC_ARM64_REG_FP,sp+0x600)):
                        u.reg_write(reg,value)
                    for reg,value in ((r.UC_ARM64_REG_S9,width*scale),(r.UC_ARM64_REG_S8,height*scale)):
                        u.reg_write(reg,struct.unpack('<I',struct.pack('<f',value))[0])
                    u.emu_start(0x3a2ea4c,0x3a2eb04,count=160)
                    require(u.reg_read(r.UC_ARM64_REG_PC)==0x3a2eb04,'Capture setup did not finish')
                    sx,sy=struct.unpack('<2f',u.mem_read(sp+0x70,8))
                    cx,cy=struct.unpack('<2f',u.mem_read(sp+0xb8,8))
                    logical=1920 if ortho else 1080*aspect
                    require(math.isclose(sx,width*scale/logical,rel_tol=2e-6),'Incorrect source width')
                    require(math.isclose(sx*cx,(panel+side)*scale/logical,abs_tol=2e-6),'Incorrect source center')
                    require(math.isclose(sy,height*scale/1080,rel_tol=2e-6) and math.isclose(sy*cy,6/1080,rel_tol=2e-6),'Vertical copy coordinates changed')
                    count+=1
    return dict(executions=count,original_coordinate_block='passed',gpu_sampling_confirmed=False)


def verify_material_projection(image):
    """Verify the game's Entire Layout mapping divides by projection scale X.

    Executes 00279700..002797B8 from the hash-verified local executable.
    That block builds texture matrix rows using DrawInfo's view matrix.
    """
    import unicorn as uc
    from unicorn import arm64_const as r
    runs=samples=0
    for width,height in ((1920,1080),(1280,720)):
        for factor in (1,43/32):
            u=uc.Uc(uc.UC_ARCH_ARM64,uc.UC_MODE_ARM)
            for page in (0x279000,0x4002000):
                u.mem_map(page,4096);u.mem_write(page,bytes(image[page:page+4096]))
            u.mem_map(0x100000,0x10000)
            params,draw=0x101000,0x102000
            u.mem_write(params,struct.pack('<4f',0,0,factor,1))
            u.mem_write(draw+0x80,struct.pack('<12f',1,0,0,0,0,1,0,0,0,0,1,0))
            u.reg_write(r.UC_ARM64_REG_X23,params);u.reg_write(r.UC_ARM64_REG_X20,draw)
            for index,value in ((0,height),(1,width),(2,height/2),(4,width/2),(8,.5)):
                u.reg_write(r.UC_ARM64_REG_S0+index,struct.unpack('<I',struct.pack('<f',value))[0])
            u.emu_start(0x279700,0x2797b8,count=100)
            require(u.reg_read(r.UC_ARM64_REG_PC)==0x2797b8,'Material projection did not finish')
            row=struct.unpack('<4f',u.reg_read(r.UC_ARM64_REG_Q1).to_bytes(16,'little'))
            require(math.isclose(row[0],1/(width*factor),rel_tol=2e-6) and row[1:]==(0,0,.5),'Unexpected game material mapping')
            for x in (-width*factor/2,-width/2,-width/4,0,width/4,width/2,width*factor/2):
                uv=row[0]*x+row[3]
                require(math.isclose(uv,.5+x/(width*factor),abs_tol=2e-6),'Source and display capture positions differ')
                samples+=1
            runs+=1
    return dict(executions=runs,coordinate_samples=samples,original_material_matrix='passed',gpu_sampling_confirmed=False)
