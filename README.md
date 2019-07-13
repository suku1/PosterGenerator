# PosterGenerator
画像を減色してSchematicファイルに変換します  

## Requires  
**使用モジュール**  
 - [numpy](https://github.com/numpy/numpy)
```bash
$ pip install numpy
```
 - [nbtlib](https://github.com/vberlier/nbtlib)  
```bash
$ pip install nbtlib
```
 - opencv-python
```bash
$ pip install opencv-python
```

## Usage  
**解像度が大きな画像は減色に時間がかかります**  
  
example.pngを変換する場合  
```bash
$ python PosterGenerator.py example.png
```

## Config  
config.jsonを書き換えることで設定を変更できます  
  
**設定項目**  
 - PALETTE_NAME  
 パレットのファイル名  
 拡張子は不要  
   
 - OUTPUT_IMAGE  
 画像の出力フォルダ  
 - OUTPUT_LIST  
 材料リストの出力フォルダ  
 - OUTPUT_SCHEMATIC  
 Schematicファイルの出力フォルダ  
 - COLOR_TYPE  
 色空間の指定(RGBまたはLAB)  
 - RGB_DIFF  
 色差をRGBで取る  
 - DITHER  
 ディザリングの有無  
 - DITHER_WEIGHT  
 ディザリング時の誤差拡散量  
 - RANDOM_DITHER  
 ディザリング時の誤差拡散に乱数を用いる  
 - SEED  
 乱数のシード値  
 Falseなら指定しない  

## Palette
paletteフォルダ内のpalette.jsonを書き換えることで生成されるSchematicファイルの使用ブロックを変更できます  
config.jsonのPALETTE_NAMEを変更すれば使用するパレットを切り替えられるので複数パレットの使い分けも可能です  
  
**paletteの設定項目**
 - COLOR_NAME  
 色の名前  
 現状使用していない  
   
 - COLOR  
 色のRGBデータ  
 - BLOCK_NAME  
 色に対応するブロックの名前  
 - BLOCK_ID  
 ブロックID  
 - DATA  
 ブロックのデータタグ  
 - USE  
 減色に使用するかどうか  
 Falseなら使用しない  
 デフォルトではすべてTrue  
  
各色に対応しているブロックは[wiki(外部リンク)](https://minecraft.gamepedia.com/Map_item_format)等で確認してください  

## Licence

MIT

## Author

[suku1](https://github.com/suku1)
