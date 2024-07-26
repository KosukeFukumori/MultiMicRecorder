import datetime
import os
import queue
import threading
import time
import tkinter
import tkinter as tk
import wave
from dataclasses import dataclass
from time import sleep
from tkinter import StringVar, Text, Tk
from tkinter.ttk import Button, Combobox, LabelFrame

import numpy as np
import sounddevice as sd
from pydub import AudioSegment


class SingleMicRecorder:
    def __init__(
        self,
        filename: str,
        device_index: int,
        fs: int = 44100,
        chunk_size: int = 2**12,
        channels: int = 2,
    ) -> None:
        # 録音パラメータ
        self._filename = filename
        self._device_index = device_index
        self._fs = fs
        self._chunk_size = chunk_size
        self._channels = channels

        # 録音データを保持するキュー
        self._chunk_queue: queue.Queue

        # 録音停止がリクエストされると True になる
        self._is_stop_requested = False

        # 録音するスレッド
        self._recording_thread: threading.Thread | None = None

    def _callback(self, indata, frames, time, status) -> None:
        """録音データをキューに追加するコールバック関数"""
        self._chunk_queue.put(indata.copy())

    def _record_to_file(self):
        """キューから録音データを取り出し、ファイルに書き込む関数"""
        with wave.open(self._filename, "wb") as wf:
            wf.setnchannels(self._channels)
            wf.setsampwidth(2)
            wf.setframerate(self._fs)

            with sd.InputStream(
                callback=self._callback,
                device=self._device_index,
                channels=self._channels,
                samplerate=self._fs,
            ):
                while not self._is_stop_requested:
                    chunk = self._chunk_queue.get()
                    wf.writeframes(
                        (chunk * np.iinfo(np.int16).max).astype(np.int16).tobytes()
                    )
                self._is_stop_requested = False

    def start_recording(self):
        if self._recording_thread is not None:
            raise RuntimeError("すでに録音スレッドが動作しています")

        self._is_stop_requested = False
        self._chunk_queue = queue.Queue()
        self._recording_thread = threading.Thread(target=self._record_to_file)
        self._recording_thread.start()

    def stop_recording(self):
        self._is_stop_requested = True
        while self._is_stop_requested:
            time.sleep(0.1)

    @dataclass
    class MicDevice:
        index: int
        name: str
        channels: int

    @staticmethod
    def get_mic_device_list() -> list[MicDevice]:
        sd._terminate()
        sd._initialize()
        devices = sd.query_devices()
        mic_devices: list[SingleMicRecorder.MicDevice] = []
        if not isinstance(devices, sd.DeviceList):
            return mic_devices
        for d in devices:
            if d.get("max_input_channels", 0) == 0:
                continue
            mic_devices.append(
                SingleMicRecorder.MicDevice(
                    index=d["index"], name=d["name"], channels=d["max_input_channels"]
                )
            )
        return mic_devices


class GUI:

    def __init__(self, savedir: str = "records"):
        self._savedir = savedir
        self._build()
        self._recorder1: SingleMicRecorder | None = None
        self._recorder2: SingleMicRecorder | None = None
        self._log("アプリを起動しました")

    def _build(self):
        root = Tk()
        root.title("録音アプリ")

        # デバイス1選択コンボボックス前のラベル
        device1_label = tk.Label(root, text="録音デバイス 1")
        device1_label.grid(row=0, column=0, padx=8, pady=8)

        # デバイス1選択コンボボックス
        self._device1_list_combobox_value = StringVar()
        self._device1_list_combobox = Combobox(
            root,
            textvariable=self._device1_list_combobox_value,
            state="readonly",
        )
        self._device1_list_combobox.grid(row=0, column=1, sticky=tk.EW, padx=8, pady=8)

        # デバイス2選択コンボボックス前のラベル
        device2_label = tk.Label(root, text="録音デバイス 2")
        device2_label.grid(row=1, column=0, padx=8)

        # デバイス2選択コンボボックス
        self._device2_list_combobox_value = StringVar()
        self._device2_list_combobox = Combobox(
            root,
            textvariable=self._device2_list_combobox_value,
            state="readonly",
        )
        self._device2_list_combobox.grid(row=1, column=1, sticky=tk.EW, padx=8)

        # デバイスリスト更新ボタン
        self._device_refresh_button = Button(
            root,
            text="デバイスリスト更新",
            command=self._on_device_refresh_button_click,
        )
        self._device_refresh_button.grid(
            row=2, column=0, columnspan=2, sticky=tk.E, padx=8
        )

        # 録音開始ボタン
        self._start_stop_button = Button(
            root,
            text="録音開始",
            command=self._on_start_recording_button_click,
        )
        self._start_stop_button.grid(row=3, column=0, columnspan=2)

        # ログ表示テキストボックス
        self.log_text_box = Text(state=tkinter.DISABLED)
        self.log_text_box.grid(
            row=4,
            column=0,
            columnspan=2,
            sticky=tk.NSEW,
            padx=8,
            pady=8,
        )

        # ウィンドウのリサイズに合わせて index のウィジェットの幅を広げる
        root.grid_columnconfigure(index=1, weight=1)
        root.grid_rowconfigure(index=4, weight=1)

        # デバイスリストを更新
        self._on_device_refresh_button_click()

        # デフォルトデバイスを設定
        devices = SingleMicRecorder.get_mic_device_list()
        device_names = [d.name for d in devices]
        if "MacBook Proのマイク" in device_names:
            self._device1_list_combobox.set("MacBook Proのマイク")
        if "BlackHole 2ch" in device_names:
            self._device2_list_combobox.set("BlackHole 2ch")

        self._root = root

    def _log(self, text: str):
        self.log_text_box.configure(state=tkinter.NORMAL)
        self.log_text_box.insert(
            "end", f"[{datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')}] {text}\n"
        )
        self.log_text_box.configure(state=tkinter.DISABLED)

    def _on_device_refresh_button_click(self):
        devices = SingleMicRecorder.get_mic_device_list()
        device_names = [d.name for d in devices]
        self._device1_list_combobox.configure(values=device_names)
        self._device2_list_combobox.configure(values=device_names)

    def _on_start_recording_button_click(self):
        self._log("録音開始ボタンが押されました")

        # デバイス選択を変更できないようにする
        self._device1_list_combobox.configure(state=tkinter.DISABLED)
        self._device2_list_combobox.configure(state=tkinter.DISABLED)
        self._device_refresh_button.configure(state=tkinter.DISABLED)

        # デバイス情報を取得
        devices = SingleMicRecorder.get_mic_device_list()
        name_to_idx = {d.name: d.index for d in devices}
        idx_to_channels = {d.index: d.channels for d in devices}
        device1_index = name_to_idx.get(self._device1_list_combobox_value.get(), -1)
        device2_index = name_to_idx.get(self._device2_list_combobox_value.get(), -1)

        # デバイスが選択されていないときの処理です
        if device1_index == -1 and device2_index == -1:
            self._log("デバイスが1つも選択されていません。録音開始を取りやめます。")
            return

        # 録音ボタンの表記を変更します
        self._start_stop_button.configure(
            text="録音停止", command=self._on_stop_recording_button_click
        )

        # 保存先ディレクトリがない場合、作成する
        if not os.path.exists(self._savedir):
            os.makedirs(self._savedir)
        datenow_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")

        if device1_index != -1:
            self._filename1 = os.path.join(self._savedir, f"{datenow_str}_1.wav")
            self._log(
                f"[{self._device1_list_combobox_value.get()}]を録音します。保存先: {self._filename1}"
            )
            self._recorder1 = SingleMicRecorder(
                filename=self._filename1,
                device_index=device1_index,
                channels=idx_to_channels[device1_index],
            )
            self._recorder1.start_recording()

        if device2_index != -1:
            self._filename2 = os.path.join(self._savedir, f"{datenow_str}_2.wav")
            self._log(
                f"[{self._device2_list_combobox_value.get()}]を録音します。保存先: {self._filename2}"
            )
            self._recorder2 = SingleMicRecorder(
                filename=self._filename2,
                device_index=device2_index,
                channels=idx_to_channels[device1_index],
            )
            self._recorder2.start_recording()

    def _on_stop_recording_button_click(self):
        self._log("録音停止ボタンが押されました")
        self._start_stop_button.configure(state=tkinter.DISABLED)

        if self._recorder1 is not None:
            self._recorder1.stop_recording()

        if self._recorder2 is not None:
            self._recorder2.stop_recording()
        self._log("録音を停止しました")

        if self._recorder1 is not None and self._recorder2 is not None:

            self._log("複数の録音を Mix 中です")
            mixed_filename = self._filename1.replace("_1.", ".")

            rec1 = AudioSegment.from_file(self._filename1)
            rec2 = AudioSegment.from_file(self._filename2)

            # ミキシングとファイル出力
            output = rec1.overlay(rec2, position=0)
            output.export(mixed_filename, format="wav")

            self._log(f"Mix 完了しました。保存先: {mixed_filename}")

        self._recorder1 = None
        self._recorder2 = None

        # デバイス選択を変更できるようにする
        self._device1_list_combobox.configure(state=tkinter.NORMAL)
        self._device2_list_combobox.configure(state=tkinter.NORMAL)
        self._device_refresh_button.configure(state=tkinter.NORMAL)

        self._start_stop_button.configure(
            text="録音開始",
            command=self._on_start_recording_button_click,
            state=tkinter.NORMAL,
        )

    def start(self):
        self._root.mainloop()


if __name__ == "__main__":
    GUI(savedir=os.path.join(os.environ["HOME"], "records")).start()
