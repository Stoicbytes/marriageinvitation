from PIL import Image, ImageFilter
import numpy as np, sys
SRC, OUT = sys.argv[1], sys.argv[2]
a = np.asarray(Image.open(SRC).convert('RGB')).astype(float)
for x0, x1 in [(33, 36), (170, 175), (849, 854), (988, 992)]:   # remove thin gold frame lines
    L, R = a[:, x0-3], a[:, x1+3]
    for i, x in enumerate(range(x0, x1+1)):
        t = (i+1)/(x1-x0+2)
        line = a[:, x].mean(1) < a[:, x0-3].mean(1) - 10
        a[line, x] = (L*(1-t) + R*t)[line]
CREAM = np.array([245, 225, 190.])

def soft(mask, r=10):
    im = Image.fromarray((mask*255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(r))
    return np.asarray(im).astype(float)/255

def cut(rgb, keep, lo=14, hi=40):
    d = np.abs(rgb - CREAM).max(2)
    al = np.clip((d-lo)/(hi-lo), 0, 1) * keep
    fg = CREAM + (rgb-CREAM)/np.maximum(np.clip((d-lo)/(hi-lo), 0, 1), 1e-3)[..., None]
    return np.dstack([np.clip(fg, 0, 255), al*255]).astype(np.uint8)

def edge_fade(h, w, top=0, bottom=0, left=0, right=0):
    yy, xx = np.mgrid[0:h, 0:w].astype(float)
    f = np.ones((h, w))
    if top: f *= np.clip(yy/top, 0, 1)
    if bottom: f *= np.clip((h-1-yy)/bottom, 0, 1)
    if left: f *= np.clip(xx/left, 0, 1)
    if right: f *= np.clip((w-1-xx)/right, 0, 1)
    return f

def save(arr, name, scale=1):
    im = Image.fromarray(arr, 'RGBA')
    if scale != 1: im = im.resize((int(im.width*scale), int(im.height*scale)), Image.LANCZOS)
    im.save(f'{OUT}/{name}.png', optimize=True)

# garland + bell
h, w = 620, 335
yy, xx = np.mgrid[0:h, 0:w]
erase = ((xx > 220) & (yy > 112)) | ((xx > 148) & (yy > 228)) | ((xx < 37) & (yy > 335))
keep = soft(1-erase, 5) * (1 - erase) * edge_fade(h, w, bottom=60, right=45)
save(cut(a[0:h, 0:w], keep, lo=np.where(yy > 300, 34, 26), hi=np.where(yy > 300, 54, 48)), 'garland')

# lamp + flowers + steps
h, w = 536, 330
yy, xx = np.mgrid[0:h, 0:w]
erase = (xx > 166) & (yy < 300)
keep = np.clip(soft(1-erase, 16)*1.6-0.6, 0, 1) * edge_fade(h, w, top=150, right=60)
save(cut(a[1000:1536, 0:330], keep, lo=24, hi=46), 'lamp')

# gopuram + palms as sepia ink
gp = a[700:1470, 740:1024]
lum = gp.mean(2); lc = CREAM.mean()
ink = np.clip((lc - lum - 3)/55, 0, 1)
yy, xx = np.mgrid[0:gp.shape[0], 0:gp.shape[1]]
ink[(xx < 112) & (yy < 330)] = 0
ink[(yy > 115) & (yy < 135) & (xx < 60)] = 0
ink *= edge_fade(*ink.shape, bottom=140, left=50)
out = np.zeros(gp.shape[:2] + (4,)); out[..., :3] = [150, 110, 60]; out[..., 3] = ink*255
save(out.astype(np.uint8), 'gopuram')

# ganesha line icon
gn = Image.fromarray(a[118:208, 468:562].astype(np.uint8)).resize((94*6, 90*6), Image.LANCZOS).filter(ImageFilter.GaussianBlur(3))
gl = np.asarray(gn).astype(float).mean(2)
al = np.clip((lc - gl - 30)/45, 0, 1)
out = np.zeros(gl.shape + (4,)); out[..., :3] = [176, 122, 42]; out[..., 3] = al*255
save(out.astype(np.uint8), 'ganesha', 0.5)
