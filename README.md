# MultiMicRecorder
- 2つのマイクデバイスを同時録音するアプリです。
- 2つの音声は、個別とMixedの両方で保存されます。
- Web会議などで、通話先の音声と、自分自身の音声を録音する際に便利です。
- Web会議を録音する場合は、Black Hole などをインストールし
  - Web会議の音声出力先を Black Hole にする
  - このアプリの録音デバイス1を自身のマイク、デバイス2を Black Hole にします。

## インストールと起動
Pythonをインストール後、必要なライブラリをインストールします：
```
pip install -r requirements.txt
```

`run.command` をダブルクリックするか（mac向け)、`python main.py` を実行してください。

## 使い方

1. 画面上部の2つのプルダウンから、録音したい2つのデバイスを選択します。
1. 録音開始ボタンを押すと、`~/records/*.wav` に保存されます。
    - ファイルは3つ生成されます（2デバイス選択時）。
    - ファイル末尾が `_1.wav`, `_2.wav` のものは個別の音声で、残りの1つはMixしたものです。
![App Image](/assets/app_img.png)

## Mac向けのWeb会議録音方法

### 前提
ここでは、次の利用を想定しています
- Web会議の視聴用デバイス = `ヘッドフォン`
- Web会議で使うマイク = `Macbook 内蔵マイク`

### 設定方法
1. [Black Hole](https://existential.audio/blackhole/) をインストールします。
2. `Audio MIDI 設定` アプリを開き、`複合出力装置`を作成します。出力先は、`Black Hole` と Web会議視聴用の`ヘッドフォン`です。
    ![MIDI Setting](/assets/midi_setting.png)
3. Web会議アプリの音声設定を以下のようにします：
    - 音声出力 = `複合出力装置` （上述のMIDIで設定したもの）
    - 音声入力 = `Macbook 内蔵マイク`
4. システム音声設定を以下のようにします：
    - 音声出力 = `ヘッドフォン`（使いたいデバイスにしておくと音量調整しやすです）
    - 音声入力 = `Black Hole` 以外
5. 本アプリを立ち上げ、録音先を `Macbook 内蔵マイク`, `Black Hole` とします。
6. 本アプリの録音ボタンを押し、Web会議に参加します。
