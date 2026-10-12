"""Targeted UI regressions; optional checks read the user's verified local NSO.

No game instructions or resource fixtures are embedded in this module.
"""
import json
import math
import struct

from build import ROOT, require


def check_ui_deltas():
    records = {r['resource']: r for r in json.loads((ROOT / 'layout_deltas.json').read_text())}
    dal = records['WipeVisitorDemo.arc/blyt/WipeVisitorDemo.bflyt']['changes']
    require(len(dal) == 4, 'DAL correction must change only the two mask scales')
    for name in ('P_Circle_00', 'P_MaruS_00'):
        changes = [c for c in dal if c['description'].startswith(name + ':')]
        require(len(changes) == 2, 'Missing uniform DAL mask scale')
        require(all(c['before'] == struct.pack('<f', 1).hex()
                    and c['after'] == struct.pack('<f', 43/32).hex() for c in changes),
                'DAL mask is not uniformly scaled')
    scale = struct.unpack('<f', bytes.fromhex(dal[0]['after']))[0]
    # At the closed endpoint, L/R meet at x=0 and cover the full height.
    require(1098 * scale >= 1290 and 1080 * scale >= 1080, 'Closed DAL mask exposes sides')
    # At the open endpoint, the circular aperture encloses every screen corner.
    require(2210 * scale / 2 >= math.hypot(1290, 540), 'Open DAL aperture clips corners')
    # L/R outside edges remain outside the display throughout the animation.
    # The original matching Hermite curves share a normalized progress value.
    require(min(2210/2, 1098) * scale >= 1290, 'DAL animated border is too narrow')
    for layout in ('LMapMini', 'LCloudIslandMapMini'):
        changes = records[f'{layout}.arc/blyt/{layout}.bflyt']['changes']
        require(len(changes) == 1 and changes[0]['before'] == '01000000'
                and changes[0]['after'] == '00000000', 'Unexpected minimap correction')
    return dict(dal_mask_geometry='passed', minimap_property_removal='passed', gameplay_confirmed=False)


def _scissor_bounds(image, viewport, center, size, scale, patches=(), aspect=43/18, orthographic=False, local=False):
    """Execute the unchanged 3.0.3 ScissorPane rectangle calculation.

    03A308C8..03A30A60 uses the pane's global matrix and the nominal
    layout size, without applying the widened UI projection. Run only after
    load_main has verified the build ID and every segment hash.
    """
    import unicorn as uc
    from unicorn import arm64_const as r
    u = uc.Uc(uc.UC_ARCH_ARM64, uc.UC_MODE_ARM)
    u.mem_map(0x3a30000, 0x2000)
    u.mem_write(0x3a30000, bytes(image[0x3a30000:0x3a32000]))
    u.mem_map(0x3f06000, 0x1000)
    for p in patches:
        if 0x3a30000 <= p['address'] < 0x3a32000 or 0x3f06000 <= p['address'] < 0x3f07000:
            u.mem_write(p['address'], p['new'])
    u.mem_map(0x100000, 0x10000)
    pane, draw, context, vp, reference, frame = (0x101000, 0x102000, 0x103000, 0x104000, 0x105000, 0x108000)
    u.mem_write(pane + 0x50, struct.pack('<2f', *size))
    for offset, value in ((0x70, scale), (0x84, scale), (0x7c, center[0]), (0x8c, center[1])):
        u.mem_write(pane + offset, struct.pack('<f', value))
    u.mem_write(draw + 0xc0, struct.pack('<Q', reference))
    u.mem_write(draw + 0x10, struct.pack('<f', 1/aspect))
    u.mem_write(draw + 0x24, struct.pack('<f', 1))
    u.mem_write(draw + 0x4c, struct.pack('<f', 1 if orthographic else 0))
    u.mem_write(context, struct.pack('<Q', vp))
    u.mem_write(reference + 0x28, struct.pack('<2f', 1920, 1080))
    u.mem_write(vp + 8, struct.pack('<2f', *viewport))
    for reg, value in ((r.UC_ARM64_REG_X19, draw), (r.UC_ARM64_REG_X21, pane),
                       (r.UC_ARM64_REG_X22, context), (r.UC_ARM64_REG_FP, frame),
                       (r.UC_ARM64_REG_X9, int(local)), (r.UC_ARM64_REG_SP, 0x10f000)):
        u.reg_write(reg, value)
    u.emu_start(0x3a308c8, 0x3a30a64, count=250)
    require(u.reg_read(r.UC_ARM64_REG_PC) == 0x3a30a64, 'Scissor calculation did not finish')
    return struct.unpack('<4f', u.mem_read(frame - 0x20, 16))


def verify_scissor_hook(config, patches):
    """Execute the new hook, including register preservation and relocation."""
    from verify import _machine, _registers
    from unicorn import arm64_const as r
    count = 0
    site = 0x3a308e8
    for base in (0, 0x7100000000):
        for aspect in (16/9, 43/18, 4/3, 32/9):
            for ortho in (False, True):
                for flags in (0, 0x90000000, 0x60000000, 0xf0000000):
                    u = _machine(patches, base)
                    draw=0x200000
                    u.reg_write(r.UC_ARM64_REG_X19, draw)
                    for i in range(32):u.reg_write(r.UC_ARM64_REG_Q0+i, (i+123)*0x123456789abcdef001122334455667)
                    for i, value in ((0,1280),(1,720),(2,1920),(4,1080)):
                        u.reg_write(r.UC_ARM64_REG_S0+i, struct.unpack('<I',struct.pack('<f',value))[0])
                    for offset,value in ((0x10,2/aspect),(0x24,2),(0x4c,int(ortho))):
                        u.mem_write(draw+offset,struct.pack('<f',value))
                    u.reg_write(r.UC_ARM64_REG_NZCV,flags)
                    before=_registers(u)
                    simd=[u.reg_read(r.UC_ARM64_REG_Q0+i) for i in range(32)]
                    u.emu_start(base+site,base+site+4,count=80)
                    require(u.reg_read(r.UC_ARM64_REG_PC)==base+site+4,'Scissor hook did not return')
                    require(_registers(u)==before,'Scissor hook changed registers/flags/stack')
                    require(all(u.reg_read(r.UC_ARM64_REG_Q0+i)==simd[i] for i in range(32) if i!=3), 'Scissor scratch SIMD not restored')
                    actual=struct.unpack('<f',struct.pack('<I',u.reg_read(r.UC_ARM64_REG_S3)))[0]
                    expected=1280/1920 if ortho else 1280/1080/aspect
                    require(math.isclose(actual,expected,rel_tol=2e-6),'Scissor conversion differs from projection')
                    count+=1
    return dict(executions=count, register_preservation='passed', orthographic_passthrough='passed', load_bases=2)


def verify_projected_scissors(image, patches):
    count=0
    # Phone pages, shifted maps, centered catalog, and scaled photo grid.
    for vp in ((1920,1080),(1280,720)):
        for center,size in (((-690,-39),(540,540)),((1076,-353),(354,290)),((0,0),(1920,1080)),((0,70),(1800,1280))):
            for scale in (1,.8,.95):
                for aspect in (43/18,16/9):
                    actual=_scissor_bounds(image,vp,center,size,scale,patches,aspect)
                    expected=[max(0,vp[0]/2+(center[0]-size[0]*scale/2)*vp[0]/(1080*aspect)),
                              max(0,vp[1]/2+(center[1]-size[1]*scale/2)*vp[1]/1080),
                              min(vp[0],vp[0]/2+(center[0]+size[0]*scale/2)*vp[0]/(1080*aspect)),
                              min(vp[1],vp[1]/2+(center[1]+size[1]*scale/2)*vp[1]/1080)]
                    # Game rounds the rectangle to integer pixels.
                    require(all(abs(a-b)<=1.01 for a,b in zip(actual,expected)),f'Incorrect projected scissor: {actual}, {expected}')
                    count+=1
        for local in (False,True):
            a=_scissor_bounds(image,vp,(-360,-39),(540,540),1,orthographic=True,local=local)
            b=_scissor_bounds(image,vp,(-360,-39),(540,540),1,patches,orthographic=True,local=local)
            require(a==b,'Capture-local or orthographic clipping changed')
            count+=1
    return dict(executions=count, phone_map_catalog_bounds='passed', capture_local_passthrough='passed', gameplay_confirmed=False)


def check_phone_menu_deltas():
    records = json.loads((ROOT/'layout_deltas.json').read_text())
    by_name = {r['resource'].split('/')[-1]:r for r in records}
    phone = by_name['MenuDevice.bflyt']['changes']
    def changed_value(changes, pane, field):
        items = [c for c in changes if c['description']==pane+': '+field]
        require(len(items)==1, 'Missing or duplicated targeted field')
        return struct.unpack('<f',bytes.fromhex(items[0]['after']))[0]
    x = changed_value(phone,'P_Base_00','horizontal position')
    require(x==-690, 'Phone edge offset is wrong')
    capture = changed_value(phone,'N_Capture_00','horizontal position')
    require(capture==x,'Capture and phone have different logical centers')
    require(not any(c['description'].startswith('N_CapDown_') for c in phone),
            'Resource preprojection would apply the shared capture correction twice')
    require(not any('Scissor' in c['description'] for c in phone), 'Phone paging clip was removed')
    for layout in ('MenuMobileBank','MenuMobileBankPoki','Catalog','NatteeCatalog','HotelCatalog','WherearenInspect','ClientListBG','CatalogBG','CatalogGiftBG','NatteeCatalogBG','HotelCatalogBG'):
        for c in by_name[layout+'.bflyt']['changes']:
            before,after=(struct.unpack('<f',bytes.fromhex(c[k]))[0] for k in ('before','after'))
            require(c['description'].startswith('P_') and c['description'].endswith(': width') and after-before==660,
                    'Menu correction changed more than background picture widths')
    for layout in ('WipeDevice','WipeDeviceLoad'):
        c=by_name[layout+'.bflyt']['changes']
        require(changed_value(c,'P_Base_00','width')==4410 and changed_value(c,'P_Base_00','height')==3408,
                'Wrong app mask closed extent')
        # Even an inscribed ellipse covers all corners at the shifted center.
        cx=changed_value(c,'P_Base_00','horizontal position')
        require(((1290-cx)/2205)**2+(543/1704)**2<1, 'Closed app mask leaves a corner exposed')
    return dict(phone_capture_alignment='passed', menu_background_only_edits='passed', app_mask_closed_coverage='passed', gameplay_confirmed=False)


def verify_scissor_regression(image):
    examples = []
    for width, height in ((1920, 1080), (1280, 720)):
        for x in (1076, 1101):
            for scale, map_height in ((1, 290), (.94, 350)):
                left, bottom, right, top = _scissor_bounds(image, (width, height),
                                                          (x, -353), (354, map_height), scale)
                map_left = width / 2 + (x - 177 * scale) * width / 2580
                map_right = width / 2 + (x + 177 * scale) * width / 2580
                visible = max(0, min(right, map_right) - max(left, map_left)) / (map_right - map_left)
                require(visible < .15, 'Regression no longer reproduces the reported missing terrain')
                examples.append(dict(viewport=[width, height], hud_x=x, scale=scale,
                                     legacy_scissor=[left, bottom, right, top],
                                     projected_terrain_x=[map_left, map_right], visible_fraction=visible))
    return dict(executions=len(examples), original_clipping_bug_reproduced=True,
                correction='Only minimap ScissorOn property registration removed; capture target bounds retained',
                examples=examples, gameplay_confirmed=False)


def verify_local_ui(directory):
    """Check the changed layouts against actual local resource structures."""
    from pathlib import Path
    records = {r['resource']: r for r in json.loads((ROOT / 'layout_deltas.json').read_text())}

    def read(layout):
        record = records[f'{layout}.arc/blyt/{layout}.bflyt']
        data = bytearray((Path(directory) / f'{layout}.bflyt').read_bytes())
        require(__import__('hashlib').sha256(data).hexdigest() == record['sha256'], 'Wrong layout for geometry check')
        for c in record['changes']:
            data[c['offset']:c['offset']+4] = bytes.fromhex(c['after'])
        panes, props, last = {}, {}, None
        at = struct.unpack_from('<H', data, 6)[0]
        while at < len(data):
            tag, length = struct.unpack_from('<4sI', data, at)
            require(length >= 8 and at + length <= len(data), 'Invalid layout section')
            if tag in (b'pan1', b'pic1', b'prt1', b'wnd1'):
                last = data[at+12:at+36].split(b'\0')[0].decode()
                panes[last] = struct.unpack_from('<10f', data, at+44)
            elif tag == b'usd1':
                count = struct.unpack_from('<H', data, at+8)[0]
                names = []
                for i in range(count):
                    entry = at + 12 + i * 12
                    start = entry + struct.unpack_from('<I', data, entry)[0]
                    names.append(data[start:data.index(0, start)].decode())
                props[last] = names
            at += length
        return panes, props

    panes, _ = read('WipeVisitorDemo')
    require(panes['P_Circle_00'][6:8] == panes['P_MaruS_00'][6:8] == (43/32, 43/32), 'Wrong mask scales')
    require(panes['N_Logo_00'][:2] == (0, 0) and panes['N_Logo_00'][6:8] == (1, 1), 'DAL logo group changed')
    require(panes['P_Logo_00'][6:] == (1, 1, 256, 256), 'DAL logo size changed')
    for layout, height in (('LMapMini', 290), ('LCloudIslandMapMini', 350)):
        panes, props = read(layout)
        require(props['N_Scissor_00'] == [], 'Screen-space clipping still registered')
        require('DynamicCaptureOn' in props['N_Capture_00'], 'Capture no longer registered')
        require('DynamicCaptureUseName' in props['P_Capture_00'], 'Capture display lost its source')
        require(panes['N_Capture_00'] == (0, 0, 0, 0, 0, 0, 1, 1, 354, height), 'Capture geometry changed')
        require(panes['P_Capture_00'] == panes['N_Capture_00'], 'Capture/display bounds differ')
    return dict(layouts=3, parsed_geometry_and_properties='passed',
                phone_menu_geometry=verify_menu_geometry(directory), gameplay_confirmed=False)


def verify_menu_geometry(directory):
    """Independently parse supplied resources and check semantics, not offsets."""
    from pathlib import Path
    from hashlib import sha256
    records=json.loads((ROOT/'layout_deltas.json').read_text())
    menu_names={'MenuMobileBank','MenuMobileBankPoki','Catalog','NatteeCatalog','HotelCatalog','WherearenInspect','ClientListBG','CatalogBG','CatalogGiftBG','NatteeCatalogBG','HotelCatalogBG'}
    layouts=curves=samples=0
    def sections(data):
        at=struct.unpack_from('<H',data,6)[0]
        while at<len(data):
            length=struct.unpack_from('<I',data,at+4)[0]
            require(length>=8 and at+length<=len(data),'Invalid resource section')
            yield data[at:at+4],data[at:at+length]
            at+=length
    def panes(data):
        result={}
        for tag,b in sections(data):
            if tag in (b'pan1',b'pic1',b'txt1',b'wnd1',b'prt1',b'bnd1'):
                result[b[12:36].split(b'\0')[0].decode()]=(tag,struct.unpack_from('<10f',b,44))
        return result
    def channels(data):
        result={}
        for tag,b in sections(data):
            if tag!=b'pai1':continue
            count=struct.unpack_from('<H',b,14)[0]; table=struct.unpack_from('<I',b,16)[0]
            for i in range(count):
                entry=struct.unpack_from('<I',b,table+4*i)[0]
                name=b[entry:entry+28].split(b'\0')[0].decode()
                for j in range(b[entry+28]):
                    tagpos=entry+struct.unpack_from('<I',b,entry+32+4*j)[0]
                    if b[tagpos:tagpos+4]!=b'FLPA' or b[entry+29]!=0:continue
                    for k in range(b[tagpos+4]):
                        c=tagpos+struct.unpack_from('<I',b,tagpos+8+4*k)[0]
                        index,target,kind,n,_,off=struct.unpack_from('<BBHHHI',b,c)
                        require(kind==2,'Unexpected pane interpolation')
                        result[(name,index,target)]=[struct.unpack_from('<3f',b,c+off+12*q) for q in range(n)]
        return result
    def hermite(a,b,t):
        span=b[0]-a[0]
        return (2*t**3-3*t**2+1)*a[1]+(t**3-2*t**2+t)*span*a[2]+(-2*t**3+3*t**2)*b[1]+(t**3-t**2)*span*b[2]
    for record in records:
        name=record['resource'].split('/')[-1];layout=name.split('.')[0]
        if not (layout in menu_names or layout=='MenuDevice' or layout.startswith('WipeInterior') or name.startswith(('WipeDevice_','WipeDeviceLoad_')) or layout in ('WipeDevice','WipeDeviceLoad')):continue
        old=(Path(directory)/name).read_bytes()
        require(sha256(old).hexdigest()==record['sha256'],'Wrong local geometry resource')
        new=bytearray(old)
        for c in record['changes']:new[c['offset']:c['offset']+4]=bytes.fromhex(c['after'])
        if old[:4]==b'FLYT':
            a,b=panes(old),panes(new);layouts+=1
            require([block for tag,block in sections(old) if tag==b'mat1']==[block for tag,block in sections(new) if tag==b'mat1'],'Material/artwork mapping changed')
            if layout in menu_names:
                for pane,(tag,values) in a.items():
                    changed=b[pane][1]
                    if changed!=values:
                        require(tag==b'pic1' and values[8]>=1920 and changed[:8]==values[:8] and changed[8]==values[8]+660 and changed[9]==values[9], 'Menu content or vertical geometry changed')
            elif layout=='MenuDevice':
                require(b['P_Base_00'][1][0]==-690 and b['P_Base_00'][1][1:]==a['P_Base_00'][1][1:],'Phone shape changed')
                for pane in a:
                    if pane not in ('P_Base_00','P_Light_00','N_Capture_00','N_CapDown_00','N_CapDown_01'):
                        require(a[pane]==b[pane],'Unexpected phone pane change')
                require(b'ScissorOn\0' in new,'Phone paging clip missing')
            elif layout.startswith('WipeInterior'):
                k=b['N_All_00'][1][6]
                require(k==43/32 and b['N_All_00'][1][7]==k,'Curtain aspect changed')
                icon=b['P_Icon_00'][1]
                require(math.isclose(icon[0]*k,1085,abs_tol=1e-4) and math.isclose(icon[1]*k,-406,abs_tol=1e-4),'Curtain icon offset wrong')
                require(all(math.isclose(s*k,1,abs_tol=1e-6) for s in icon[6:8]),'Curtain icon stretched')
                intervals=sorted(((b[f'P_Base_{i:02}'][1][0]-b[f'P_Base_{i:02}'][1][8]/2)*k,(b[f'P_Base_{i:02}'][1][0]+b[f'P_Base_{i:02}'][1][8]/2)*k) for i in range(8))
                require(intervals[0][0]<=-1290 and intervals[-1][1]>=1290 and all(x[1]>=y[0] for x,y in zip(intervals,intervals[1:])),'Curtain columns leave gaps')
                require(min(b[f'P_Base_{i:02}'][1][9]*k for i in range(8))>=1080,'Curtain height too small')
            else:
                for pane in a:
                    if pane!='P_Base_00':require(a[pane]==b[pane],'App logo/content changed')
        elif old[:4]==b'FLAN' and name.startswith(('WipeDevice_','WipeDeviceLoad_')):
            a,b=channels(old),channels(new)
            for key,keys in a.items():
                after=b[key]
                if key[0]!='P_Base_00' or key[2] not in (0,8,9):
                    require(after==keys,'App artwork animation changed');continue
                require([v[0] for v in keys]==[v[0] for v in after],'Animation timing changed')
                if key[2]==0:
                    require(all(y[1]==x[1]-330 and y[2]==x[2] for x,y in zip(keys,after)),'App mask origin does not follow phone');continue
                maximum=2940 if key[2]==8 else 2272
                require(all(y[1]==(x[1]*1.5 if x[1]==maximum else x[1]) for x,y in zip(keys,after)),'Phone-sized animation endpoint changed')
                for i in range(len(keys)-1):
                    a0,a1=keys[i:i+2]; b0,b1=after[i:i+2]
                    if a1[0]==a0[0]:continue
                    factor=(b1[1]-b0[1])/(a1[1]-a0[1]) if a1[1]!=a0[1] else 1
                    for t in (0,.125,.5,.875,1):
                        expected=b0[1]+(hermite(a0,a1,t)-a0[1])*factor
                        require(math.isclose(hermite(b0,b1,t),expected,abs_tol=.001),'Resized Hermite curve is inconsistent with endpoints')
                        samples+=1
                    curves+=1
    return dict(layouts=layouts, animated_segments=curves, interpolated_samples=samples, foreground_and_materials_preserved='passed')
