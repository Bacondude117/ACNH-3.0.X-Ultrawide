"""Coverage and foreground-preservation checks for the v3 UI sweep."""
import hashlib
import json
from pathlib import Path
import struct

from build import ROOT, require

BACKGROUND_TARGETS = {
    'MenuRecipe': ('P_Base_00','P_Tex_00'),
    'MenuPointQuestList': ('P_Tex_00','P_TitleBase_00'),
    'MenuPointTopBar': ('P_BtmFrame_00','P_BtmFrame_01'),
    'MenuBook': ('P_Base_00','P_Wipe_00'),
    'MenuBookDetail': ('P_Base_00','P_Wipe_00'),
    'MenuMapFull': ('P_Base_00',),
    'MenuProfileBg': ('P_Bg_00','P_Bg_01'),
    'LCmnBg': ('P_Bg_00','P_Bg_01','P_Dot_00'),
    'MenuChatLog': ('P_BG_00','P_CaptureMask_00','P_CaptureDown_00'),
    'MenuLoadTips': ('P_BG_00','P_CaptureMask_00','P_CaptureDown_00'),
}


def check_sweep():
    records=json.loads((ROOT/'layout_deltas.json').read_text())
    layouts={r['resource'].split('/')[-1]:r for r in records}
    for layout,panes in BACKGROUND_TARGETS.items():
        changes=layouts[layout+'.bflyt']['changes']
        for pane in panes:
            c=[c for c in changes if c['description']==pane+': width']
            require(len(c)==1,'Missing screenshot background target')
            old,new=(struct.unpack('<f',bytes.fromhex(c[0][k]))[0] for k in ('before','after'))
            require(new-old==660 and new>=2580,'Background still narrower than the wide display')
    # These are distinct modes, not animation interpolation to be shifted as a whole.
    for layout in ('MyDesignList','CloudIslandMyDesignList'):
        c=layouts[layout+'.bflyt']['changes']
        position=[c for c in c if c['description']=='N_InOut_01: horizontal position']
        require(len(position)==1 and position[0]['after']==struct.pack('<f',-425).hex(),'Left design panel anchor is wrong')
        require(not any(c['description'].startswith(('P_Base_01:', 'RootPane:', 'L_ItemBalloon_00:')) for c in layouts[layout+'.bflyt']['changes']),
                'Design panel or independent tooltip changed size/position')
    capture_changes=[c for r in records for c in r['changes'] if c['description'].endswith(': capture projection scale X')]
    require(len(capture_changes)==8,'Expected eight full-capture material projectors')
    require(all(c['before']==struct.pack('<f',1).hex() and c['after']==struct.pack('<f',43/32).hex() for c in capture_changes),
            'Full-capture material scale does not match source width')
    return dict(screenshot_background_layouts=len(BACKGROUND_TARGETS),capture_material_projectors=len(capture_changes),
                centered_content_policy='preserved',gameplay_confirmed=False)


def verify_local_sweep(directory):
    records=json.loads((ROOT/'layout_deltas.json').read_text())
    baseline_names={'Fade','Load','LoadGoOut','WipeCircle','WipeVisitorDemo','MainScreenSmartPhone','MainScreenCameraGuide',
        'MapMini','CloudIslandMapMini','LMapMini','LCloudIslandMapMini','LClock','MainScreen','KeyGuide','SaveIcon','MenuDevice',
        'MenuMobileBank','MenuMobileBankPoki','Catalog','NatteeCatalog','HotelCatalog','WherearenInspect','ClientListBG','CatalogBG',
        'CatalogGiftBG','NatteeCatalogBG','HotelCatalogBG','WipeInterior','WipeInteriorStudio','WipeInteriorWherearenIslands',
        'WipeInteriorCloudIsland','WipeInteriorHotelRoom','WipeDevice','WipeDeviceLoad'}
    layouts=embedded=materials=0
    def blocks(data):
        pos=struct.unpack_from('<H',data,6)[0]
        while pos<len(data):
            n=struct.unpack_from('<I',data,pos+4)[0]
            require(n>=8 and pos+n<=len(data),'Invalid resource section')
            yield data[pos:pos+4],pos,data[pos:pos+n]
            pos+=n
    for record in records:
        name=record['resource'].split('/')[-1]
        if not name.endswith('.bflyt') or name[:-6] in baseline_names:continue
        old=(Path(directory)/name).read_bytes()
        require(hashlib.sha256(old).hexdigest()==record['sha256'],'Unexpected sweep layout')
        new=bytearray(old)
        for c in record['changes']:new[c['offset']:c['offset']+4]=bytes.fromhex(c['after'])
        layouts+=1
        recognized=set()
        for tag,pos,b in blocks(old):
            if tag in (b'pan1',b'pic1',b'prt1',b'txt1',b'wnd1'):
                pane=b[12:36].split(b'\0')[0].decode()
                a=struct.unpack_from('<10f',b,44);z=struct.unpack_from('<10f',new,pos+44)
                for i,(x,y) in enumerate(zip(a,z)):
                    if x==y:continue
                    recognized.add(pos+44+i*4)
                    if i==8:
                        require(tag in (b'pic1',b'pan1') and x>=1880 and y==x+660,'Foreground width changed')
                    elif i==0:
                        require(name=='CameraGuide.bflyt' and abs(y-x)==330 or name in ('MyDesignList.bflyt','CloudIslandMyDesignList.bflyt') and pane=='N_InOut_01' and x==-95 and y==-425,'Unexpected position change')
                    else:
                        require(name=='CameraGuide.bflyt' and pane=='P_ModeTransitionWipe_01' and i in (6,7) and x==1 and y==43/32,'Foreground size/rotation changed')
                if tag==b'prt1':
                    count=struct.unpack_from('<I',b,84)[0]
                    part=b[96+count*40:].split(b'\0')[0]
                    for j in range(count):
                        e=96+j*40;sub=struct.unpack_from('<I',b,e+28)[0]
                        if not sub:continue
                        length=struct.unpack_from('<I',b,sub+4)[0]
                        if old[pos+sub:pos+sub+length]==new[pos+sub:pos+sub+length]:continue
                        require(part==b'LCmnBg' and b[sub:sub+4]==b'pic1','Changed an unrelated embedded part')
                        a=struct.unpack_from('<10f',b,sub+44);z=struct.unpack_from('<10f',new,pos+sub+44)
                        require(a[:8]==z[:8] and a[8:]==(1920,1080) and z[8:]==(2580,1080),'Embedded foreground changed')
                        recognized.add(pos+sub+76);embedded+=1
            elif tag==b'mat1':
                for c in record['changes']:
                    if pos<=c['offset']<pos+len(b):
                        require(c['description'].endswith(': capture projection scale X'),'Unapproved material edit')
                        recognized.add(c['offset']);materials+=1
        require(recognized=={c['offset'] for c in record['changes']},'Sweep delta did not resolve to its intended structure')
    return dict(layouts=layouts,embedded_background_overrides=embedded,capture_material_projectors=materials,
                foreground_dimensions_and_other_fields='preserved',gameplay_confirmed=False)
