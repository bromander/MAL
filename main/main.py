import tkinter as tk
from fileinput import close
from tkinter import ttk
import json
from tkinter import filedialog
import os
import tempfile
from pathlib import Path
from io import BytesIO
import glob
from PIL import Image, ImageTk

class Gui:
    def create_window(self) -> None:
        global root
        global items_frame
        global view_frame
        global data_name_label
        global data_label
        global data_label_hash
        global text_Text
        global scroll
        global music_button
        global image_label
        global export_button

        root = tk.Tk()
        root.title("MMG")
        root.geometry("800x600")

        items_frame = tk.Frame(root, bg="white", bd=5, relief=tk.RIDGE)
        items_frame.pack(side="left", fill=tk.Y)
        items_frame.pack_propagate(False)
        items_frame.configure(width=350, height=350)

        view_frame = tk.Frame(root, bg="white", bd=5, relief=tk.RIDGE)
        view_frame.pack(side="left", fill="both", expand=True)
        view_frame.pack_propagate(False)
        view_frame.configure(width=450, height=500)

        try:
            self.create_tree(self.get_path([("json", "*.json;*.JSON"), ("All files", "*.*")]))
        except FileNotFoundError:
            close()

        root.config(menu=self.create_menu())

        data_name_label = tk.Label(view_frame)
        data_label = tk.Label(view_frame)
        data_label_hash  = tk.Label(view_frame)
        text_Text = tk.Text(view_frame)
        scroll = tk.Scrollbar(view_frame, command=text_Text.yview)
        music_button = tk.Button(view_frame)
        image_label = tk.Label(view_frame)
        export_button = tk.Button(view_frame)

        root.mainloop()

    @staticmethod
    def get_path(filetypes) -> str:
        global path

        path = filedialog.askopenfilename(
            title="Choose file",
            filetypes=filetypes
        )
        return path


    def clear_temp(self):
        temp_dir = tempfile.gettempdir()
        pattern = os.path.join(temp_dir, "*.mp3")

        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print("Удалил:", file)
            except OSError as e:
                print("Не удалось удалить:", file, "-", e)

        pattern = os.path.join(temp_dir, "*.png")

        for file in glob.glob(pattern):
            try:
                os.remove(file)
                print("Удалил:", file)
            except OSError as e:
                print("Не удалось удалить:", file, "-", e)

    @staticmethod
    def get_folder(filetypes, defaultextension) -> str:

        initialfile = ''.join(path.split("/")[-1:])

        export_path = filedialog.asksaveasfilename(
            defaultextension=defaultextension,
            initialdir="/",
            initialfile=''.join(initialfile.split(".")[:-1]),
            filetypes=filetypes,
            title="Save file as"
        )
        return export_path


    def create_menu(self):
        file_menu = tk.Menu(tearoff=0)
        file_menu.add_command(label="Open", command=self.create_window)
        file_menu.add_command(label="Clear Temp", command=self.clear_temp)

        main_menu = tk.Menu(bg="white", bd=5, relief=tk.RIDGE)

        main_menu.add_cascade(label="File", menu=file_menu)

        return main_menu

    class Create_dict_tree:
        def insert_path(self, tree: ttk.Treeview, path: str, node_map: dict,
                        info: dict | None = None, root=""):
            """
            Разбивает path по '/', создаёт в tree ветки и вставляет лист.
            info — словарь с ключами 'hash' и 'size' для файла (или None для папок).
            node_map — кэш {tuple(частей пути): iid}.
            root — iid родителя ("" — корень Treeview).
            """
            parts = path.split('/')
            parent = root

            for depth, part in enumerate(parts):
                key = tuple(parts[: depth + 1])
                if key not in node_map:
                    # если это последний элемент пути и есть info — передаём в values
                    if depth == len(parts) - 1 and info is not None:
                        iid = tree.insert(parent, 'end',
                                          text=part,
                                          open=False,
                                          values=(info.get("hash"), info.get("size")))
                    else:
                        iid = tree.insert(parent, 'end',
                                          text=part,
                                          open=False)
                    node_map[key] = iid

                parent = node_map[key]

            return parent  # iid вставленного узла

        def build_tree_from_dict(self, tree: ttk.Treeview, data: dict):
            """
            data:
            {
              'minecraft': {
                 'sounds/.../click7.ogg': {'hash': '...', 'size': 123},
                 ...
              },
              ...
            }
            """
            node_map = {}

            for top_key, subdict in data.items():
                top_iid = tree.insert("", "end",
                                      text=top_key,
                                      open=True)
                node_map[(top_key,)] = top_iid

                for rel_path, info in subdict.items():
                    full_path = f"{top_key}/{rel_path}"
                    self.insert_path(tree, full_path, node_map, info, root="")


    def create_tree(self, path):

        with open(path, "r", encoding="UTF-8") as file_pon:
            file_pon = dict(json.load(file_pon))

        tree = ttk.Treeview(items_frame, show="tree")

        tree.bind("<Double-1>", self.on_select)

        vsb = tk.Scrollbar(items_frame, orient="vertical", command=tree.yview)
        vsb.pack(side=tk.LEFT, fill=tk.Y)
        tree.pack(expand=1, fill=tk.BOTH)

        tree.configure(yscrollcommand=vsb.set)

        self.Create_dict_tree().build_tree_from_dict(tree, file_pon)

    def on_select(self, event):
        tree = event.widget

        sel = tree.selection()

        if sel:
            item_id = sel[0]
            text = tree.item(item_id, "text")
            values = tree.item(item_id, "values")
            if "." in text:
                self.set_data_view_frame(text, values)


    def export_file(self, file_type, file_pon_path_old):
        path = self.get_folder([(file_type, f"*.{file_type}"), ("All files", "*.*")], f".{file_type}")
        with open(file_pon_path_old, "rb") as old_file: #i am old!
            old_file = old_file.read()

        with open(path, "wb") as new_file:
            new_file.write(old_file)



    def set_data_view_frame(self, text, values):
        global data_name_label
        global data_label
        global data_label_hash
        global text_Text
        global scroll
        global music_button
        global image_label
        global export_button

        data_name_label.destroy()
        data_label.destroy()
        data_label_hash.destroy()
        text_Text.destroy()
        scroll.destroy()
        music_button.destroy()
        image_label.destroy()
        export_button.destroy()

        data_name_label = tk.Label(view_frame, text=text, background=view_frame.cget("bg"))
        data_name_label.pack(pady=10)


        view_frame.update_idletasks()
        data_label_hash = ttk.Label(view_frame,
                               text=f"Hash: {values[0]}",
                               justify='left',
                               font=("Arial", 10),
                               background=view_frame.cget("bg"),
                               cursor="hand2"
                               )
        data_label_hash.pack(ipady=0, padx=5, anchor='nw')
        data_label_hash.bind("<Button-1>", lambda e: self.copy_to_clipboard(values[0]))

        data_label = ttk.Label(view_frame,
                               text=f"Size: {values[1]} bytes",
                               justify='left',
                               wraplength=view_frame.winfo_width() - 50,
                               font=("Arial", 10),
                               background=view_frame.cget("bg")
                               )
        data_label.pack(pady=0, padx=5, anchor='nw')

        file_name_pon = '/'.join(path.split("/")[:-2]) + "/objects"

        def find_files(root, filename):
            for dirpath, dirs, files in os.walk(root):
                if filename in files:
                    return os.path.join(dirpath, filename)

        now_file_path = str(find_files(file_name_pon, values[0]))

        try:
            export_button = tk.Button(view_frame, text="Export", command=lambda: self.export_file(text.split(".")[-1:][0], now_file_path))
            export_button.pack(ipady=5)
        except ValueError:
            exit()

        if text.split(".")[-1:][0] == "mp3" or text.split(".")[-1:][0] == "ogg" or text.split(".")[-1:][0] == "wav":
            music_button = tk.Button(view_frame, text="Play", pady=5, command= lambda: self.play_sound(now_file_path))
            music_button.pack()


        elif text.split(".")[-1:][0] == "png" or text.split(".")[-1:][0] == "jpg" or text.split(".")[-1:][0] == "jpeg":
            image_path = self.show_image(now_file_path)
            img = Image.open(image_path)
            img.thumbnail((550, 550), Image.Resampling.LANCZOS)
            photo = ImageTk.PhotoImage(img)
            image_label = tk.Label(view_frame, image=photo)
            image_label.pack(padx=10, pady=10)
            image_label.image = photo


        elif text.split(".")[-1:][0] == "json" or text.split(".")[-1:][0] == "mcmeta":

            with open(now_file_path, "r", encoding="UTF-8") as now_file:
                now_file = dict(json.load(now_file))
                pretty = json.dumps(now_file, indent=4, ensure_ascii=False, sort_keys=True)

            text_Text = tk.Text(view_frame, height=len(now_file.keys()), width=1920, borderwidth=0, background=root.cget("bg"), font=("Consolas", 10))
            scroll = tk.Scrollbar(view_frame, command=text_Text.yview)
            scroll.pack(side=tk.RIGHT, fill=tk.Y)
            text_Text.config(yscrollcommand=scroll.set)

            text_Text.pack(expand=1, fill="both")

            text_Text.insert(tk.END, pretty)
            text_Text.config(state=tk.DISABLED)


        else:
            print(f"file not found: {text.split(".")[-1:][0]}")


    def copy_to_clipboard(self, hash):
        root.clipboard_clear()
        root.clipboard_append(hash)
        root.update()  # нужно для некоторых ОС

    def play_sound(self, path):
        print(path)
        bs = BytesIO(open(path, "rb").read())

        bs.seek(0)
        # создаём временный файл с нужным расширением (например, .mp3)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(bs.read())
            tmp.flush()
            tmp_path = Path(tmp.name)

        # запускаем файл через ассоциированную программу
        os.startfile(str(tmp_path))

    def show_image(self, path):

        bs = BytesIO(open(path, "rb").read())

        bs.seek(0)
        # создаём временный файл с нужным расширением (например, .mp3)
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as tmp:
            tmp.write(bs.read())
            tmp.flush()
            tmp_path = Path(tmp.name)

        return tmp_path




def main():
    global work_with_gppic

    gui = Gui()

    gui.create_window()


if __name__ == "__main__":
    main()