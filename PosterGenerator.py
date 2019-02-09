import sys, os, json
import numpy as np
import cv2
from nbtlib import nbt
from nbtlib import tag

class poster:
    def __init__(self, name):
        self.schematic = nbt.load('original')

        try:
            self.read_img(name)
        except:
            sys.stderr.write('画像の取得に失敗\n')
            sys.exit(1)

        try:
            self.get_config()
        except:
            sys.stderr.write('設定の取得に失敗\n')
            sys.exit(1)

        try:
            self.get_color()
        except:
            sys.stderr.write('パレットデータの取得に失敗\n')
            sys.exit(1)

        self.imgname = 'converted.png' 
        self.schname = 'converted.schematic'

        self.blocks = []
        self.data = []
        if self.color_type == 'HSV':
            self.img_hsv = cv2.cvtColor(self.img, cv2.COLOR_BGR2HSV)
            self.add_hsv_palette()
        elif self.color_type == 'LAB':
            self.img_lab = cv2.cvtColor(self.img, cv2.COLOR_BGR2LAB)
            self.add_lab_palette()

    def add_hsv_palette(self):
        palette = np.zeros((1, len(self.colordata), 3), np.uint8)
        for i in range(len(self.colordata)):
            palette[0][i] = self.colordata[i]['COLOR']
        hsv = cv2.cvtColor(palette, cv2.COLOR_BGR2HSV)
        for i in range(len(self.colordata)):
            self.colordata[i]['HSV'] = [int(hsv[0][i][0]), int(hsv[0][i][1]), int(hsv[0][i][2])]

    def add_lab_palette(self):
        palette = np.zeros((1, len(self.colordata), 3), np.uint8)
        for i in range(len(self.colordata)):
            palette[0][i] = self.colordata[i]['COLOR']
        lab = cv2.cvtColor(palette, cv2.COLOR_BGR2LAB)
        for i in range(len(self.colordata)):
            self.colordata[i]['LAB'] = [int(lab[0][i][0]), int(lab[0][i][1]), int(lab[0][i][2])]

    def read_img(self, name):
        self.img = cv2.imread(name)
        self.length, self.width = self.img.shape[:2]
        pix_num = self.length * self.width
        self.progress = (
            np.arange(0, pix_num + 1, np.round(pix_num / 100), 
            dtype=int)[1:] - 1
            ).tolist()
        print('\n画像取得')
        print('  ' + name)
        print(
            '  ' + str(self.length), 
            '*', str(self.width), 
            '=', str(pix_num), 
            'pixels'
        )
        print('')

    def get_config(self):
        with open('config.json', 'r', encoding='utf-8') as f:
            config = json.load(f)
        self.color_type = config['COLOR_TYPE']
        self.rgb_diff = config['RGB_DIFF']
        self.palette_name = config['PALETTE_NAME']
        self.outimage = config['OUTPUT_IMAGE']
        self.outschematic = config['OUTPUT_SCHEMATIC']
        self.dither = config['DITHER']
        self.dither_weight = min(max(config['DITHER_WEIGHT'], 0), 1)
        self.random_dither = config['RANDOM_DITHER']
        self.seed = config['SEED']
        if self.seed:
            np.random.seed(config['SEED'])
        
        print('設定取得')
        if self.color_type == 'LAB':
            print('  色空間: LAB')
            print('  色差にRGB値を使用: ' + str(self.rgb_diff))
        elif self.color_type == 'HSV':
            print('  色空間: HSV')
            print('  色差にRGB値を使用' + str(self.rgb_diff))
        else:
            print('  色空間: RGB')
        print('  ディザリング: ' + str(self.dither))
        if self.dither:
            print('  誤差拡散量: ' + str(self.dither_weight))
            print('  誤差拡散のランダム化: ' + str(self.random_dither))
            if self.random_dither:
                print('  Seed値: ' + str(self.seed))
        print('')

    def get_color(self):
        if self.palette_name[-5:] == '.json':
            name = self.palette_name
        else:
            name = self.palette_name + '.json'
        address = os.path.join('palette', name)
        with open(address, 'r', encoding='utf-8') as f:
            self.colordata = json.load(f)
        
        use = 0
        for d in self.colordata:
            if d['USE'] == True:
                use += 1

        print('パレットデータ取得')
        print('  ' + address)
        print('  使用色数: ' + str(use) + '/' + str(len(self.colordata)))
        print('')
    
    def add_data(self, data):
        self.blocks.append(data['BLOCK_ID'])
        self.data.append(data['DATA'])

    def dithering(self):
        sys.stdout.write('減色中[0%]')
        sys.stdout.flush()
        if self.dither:
            self.floyd()
        else:
            self.no_dither()
        sys.stdout.write('\r減色完了    \n\n')
        sys.stdout.flush()

    def no_dither(self):
        count = 0
        new_img = self.get_image()
        for x in range(self.length):
            for y in range(self.width):
                new_color, diff, color_data = self.near(new_img[x][y])
                new_img[x][y] = new_color
                self.add_data(color_data)
                self.show_progress(count)
                count += 1
        new_img = self.to_gbr(new_img)
        self.img = new_img

    def floyd(self):
        count = 0
        new_img = self.get_image()
        for x in range(self.length):
            for y in range(self.width):
                new_color, diff, color_data = self.near(new_img[x][y])
                new_img[x][y] = new_color
                self.add_data(color_data)
                diff = diff / 16 * self.dither_weight
                if self.random_dither:
                    w = self.random_array(4, 16)
                else:
                    w = [7, 5, 1, 3]
                if y < self.width - 1:
                    new_img[x][y+1] = self.add_diff(new_img[x][y+1], w[0], diff)
                if x < self.length - 1:
                    new_img[x+1][y] = self.add_diff(new_img[x+1][y], w[1], diff)
                if x < self.length - 1 and y < self.width - 1:
                    new_img[x+1][y+1] = self.add_diff(new_img[x+1][y+1], w[2], diff)
                if 0 < y and x < self.length - 1:
                    new_img[x+1][y-1] = self.add_diff(new_img[x+1][y-1], w[3], diff)
                self.show_progress(count)
                count += 1
             
        new_img = self.to_gbr(new_img)
        self.img = new_img

    def show_progress(self, count):
        if count in self.progress:
            per = (self.progress.index(count) + 1)
            sys.stdout.write('\r減色中[' + str(per) + '%]')
            sys.stdout.flush()

    def add_diff(self, color, w, diff):
        for i in range(3):
            color[i] = min(max(color[i] + np.round(w * diff[i]), 0), 255)
        return color

    def near(self, old_color):
        tp = self.color_type
        if self.rgb_diff:
            if tp == 'LAB':
                temp = np.array([[old_color]], np.uint8)
                temp = cv2.cvtColor(temp, cv2.COLOR_BGR2LAB)[0][0]
                new_color, diff, color_data = self.near_lab(temp)
                new_color = np.array([[new_color]], np.uint8)
                new_color = cv2.cvtColor(new_color, cv2.COLOR_LAB2BGR)[0][0]
            elif tp == 'HSV':
                temp = np.array([[old_color]], np.uint8)
                temp = cv2.cvtColor(temp, cv2.COLOR_BGR2HSV)[0][0]
                new_color, diff, color_data = self.near_hsv(temp)
                new_color = np.array([[new_color]], np.uint8)
                new_color = cv2.cvtColor(new_color, cv2.COLOR_HSV2BGR)[0][0]
            else:
                new_color, diff, color_data = self.near_bgr(old_color)

            new_color = np.array(new_color, int)
            old_color = np.array(old_color, int)
            diff = np.array(old_color - new_color, int)
            return new_color, diff, color_data
        else:
            if tp == 'LAB':
                return self.near_lab(old_color)
            elif tp == 'HSV':
                return self.near_hsv(old_color)
            else:
                return self.near_bgr(old_color)

    def near_bgr(self, old_color):
        best = float('inf')
        new_color = []
        for d in self.colordata:
            if d['USE'] == False:
                continue
            p_color = d['COLOR']
            diff = old_color - p_color
            diff_dist = sum(diff ** 2)
            if best > diff_dist:
                best = diff_dist
                diff_re = diff
                new_color = p_color
                color_data = d
                if best == 0:
                    break
        return new_color, diff_re, color_data

    def near_lab(self, old_color):
        best = float('inf')
        new_color = []
        for d in self.colordata:
            if d['USE'] == False:
                continue
            p_color = d['LAB']
            diff = old_color - p_color
            diff_dist = sum(diff ** 2)
            if best > diff_dist:
                best = diff_dist
                diff_re = diff
                new_color = p_color
                color_data = d
                if best == 0:
                    break
        return new_color, diff_re, color_data

    def near_hsv(self, old_color):
        best = float('inf')
        new_color = []
        for d in self.colordata:
            if d['USE'] == False:
                continue
            p_color = d['HSV']            
            rp = p_color[0] / 127.5 * np.pi
            ro = old_color[0] / 127.5 * np.pi
            o = [old_color[0] / 255, old_color[1] / 255, old_color[2] / 255]
            p = [p_color[0] / 255, p_color[1] / 255, p_color[2] / 255]
            diff = np.array([
                np.sin(rp) * o[1] * o[2] - np.sin(ro) * p[1] * p[2],
                np.cos(rp) * o[1] * o[2] - np.cos(ro) * p[1] * p[2],
                o[2] - p[2]
            ])
            diff_dist = diff[0] ** 2 + diff[1] ** 2 + diff[2] ** 2
            diff = p_color - old_color
            if best > diff_dist:
                best = diff_dist
                diff_re = diff
                new_color = p_color
                color_data = d
                if best == 0:
                    break
        return new_color, diff_re, color_data

    def get_image(self):
        if self.rgb_diff:
            return self.img.copy()
        tp = self.color_type
        if tp == 'LAB':
            return self.img_lab.copy()
        elif tp == 'HSV':
            return self.img_hsv.copy()
        else:
            return self.img.copy()

    def to_gbr(self, img):
        if self.rgb_diff:
            return img
        tp = self.color_type
        if tp == 'LAB':
            return cv2.cvtColor(img, cv2.COLOR_LAB2BGR)
        elif tp == 'HSV':
            return cv2.cvtColor(img, cv2.COLOR_HSV2BGR)
        else:
            return img

    def random_array(self, num, total):
        ary = np.zeros(num, int)
        for i in range(total):
            ary[np.random.randint(0, num)] += 1
        return np.sort(ary)[::-1]

    def packing(self):
        self.schematic.root['Blocks'] = tag.ByteArray(self.blocks)
        self.schematic.root['Data'] = tag.ByteArray(self.data)
        self.schematic.root['Width'] = tag.Short(self.width)
        self.schematic.root['Length'] = tag.Short(self.length)

    def save_img(self):
        address = os.path.join(self.outimage, self.imgname)
        cv2.imwrite(address, self.img)
        print('変換後の画像を保存')
        print('  ' + address)

    def save_schematic(self):
        address = os.path.join(self.outschematic, self.schname)
        self.schematic.save(address)
        print('Schematicファイルを保存')
        print('  ' + address)

    def output(self):
        self.packing()
        try:
            self.save_img()
        except:
            sys.stderr.write('画像の保存に失敗\n')
        print('')
        try:
            self.save_schematic()
        except:
            sys.stderr.write('Schematicファイルの保存に失敗\n')  

def main():
    print('PosterGenerator')

    if len(sys.argv) == 1:
        print('')
        print('使い方')
        print('')
        print('poster.pyの場合')
        print('python poster.py example.png')
        print('')
        print('poster.exeの場合')
        print('poster.exe example.png')
    else:
        name = sys.argv[1]
        #name = 'aichan.png'
        p = poster(name)
        p.dithering()
        p.output()

    print('\n')
    print('キーを押すと終了します')
    input()
    sys.exit(0)

if __name__ == '__main__':
    main()
