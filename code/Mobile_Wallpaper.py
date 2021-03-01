from PIL import Image,ImageFilter
import time,os
import random

def save_mobile(img_in,time_data,t):
    #原图高斯模糊后裁剪固定区域
    w,h=img_in.size
    x1=random.randint(w//6,w//2)
    y1=random.randint(h//6,h//2)
    x2=x1+222
    y2=y1+20/9*(x2-x1)

    while(y2>h)or(y2<y1):
        x1=random.randint(w//6,w//2)
        y1=random.randint(h//6,h//2)
        x2=x1+222
        y2=y1+20/9*(x2-x1)

    region=(x1,y1,x2,int(y2))
    img1=img_in.crop(region)
    img1=img1.filter(ImageFilter.GaussianBlur(radius=15))
    img1=img1.resize((1080,2400))
    img2=img_in.crop(region)
    img2=img2.filter(ImageFilter.GaussianBlur(radius=15))
    img2=img2.resize((1080,2400))
    #修改图片尺寸
    demo=img_in.resize((1020,int(1020*h/w)))
    #壁纸覆盖
    img1.paste(demo,(30,455))
    #PIL保存图片
    time_data=time_data+1
    img1.save(newpath+'MW_'+str(time_data)+str(t)+'.jpg',quality=95,subsampling=0)

if __name__=='__main__':
    time_data=int(time.time())*1000
    path="d:/pictures/input/"
    newpath='d:/pictures/output/'
    t=100
    dirs=os.listdir(path)
    for filename in dirs:
        t+=1
        img_in=Image.open(path+filename)
        if ('.png' in filename):
            img_in=img_in.convert('RGB')
        save_mobile(img_in,time_data,t)