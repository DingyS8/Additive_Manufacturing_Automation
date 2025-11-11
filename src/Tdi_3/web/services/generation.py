from PIL import Image, ImageDraw
import os, shutil, trimesh

def text_to_png(text: str, out_path: str, w=1024, h=1024):
    img = Image.new("RGBA", (w,h), (10,12,40,255))
    drw = ImageDraw.Draw(img)
    drw.text((40,40), text[:3000], fill=(230,236,255,255))
    img.save(out_path)
    return out_path

def triposr_image_to_obj(preprocess, generate, pil_img, out_path_obj, do_remove_background=True, foreground_ratio=0.85):
    pre = preprocess(pil_img, do_remove_background=do_remove_background, foreground_ratio=foreground_ratio)
    obj_path, *_ = generate(pre, mc_resolution=320, formats=["obj"])
    if obj_path != out_path_obj:
        shutil.copyfile(obj_path, out_path_obj)
    return out_path_obj

def obj_to_stl(obj_path, stl_path):
    mesh = trimesh.load(obj_path)
    mesh.export(stl_path)
    return stl_path
