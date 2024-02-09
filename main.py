#!/usr/bin/python3
import pathlib
import pygubu
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import os
import pandas as pd
import analytics
from pandastable import Table, TableModel


import fitz
from PIL import Image, ImageTk  
from tkPDFViewer import tkPDFViewer as pdf
from io import BytesIO
import ini

PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "merger_gui.ui"

start_time_str = {"%d.%m.%Y %H:%M:%S" : "01.01.2000 00:00:01", 
                    "%Y-%m-%d %H:%M:%S" : "2000-01-01 00:00:01",
                    "%Y/%m/%d %H:%M:%S %r" : "2000/01/01 00:00 AM",}
end_time_str = {"%d.%m.%Y %H:%M:%S" : "01.01.2100 00:00:00", 
                    "%Y-%m-%d %H:%M:%S" : "2100-01-01 00:00:00",
                    "%Y/%m/%d %H:%M:%S %r" : "2100/01/01 00:00 AM",}


class EntryPopup(tk.Entry):

    def __init__(self, parent, iid, text, **kw):
        ''' If relwidth is set, then width is ignored '''
        super().__init__(parent, **kw)
        self.tv = parent
        self.iid = iid

        self.insert(0, text) 
        # self['state'] = 'readonly'
        # self['readonlybackground'] = 'white'
        # self['selectbackground'] = '#1BA1E2'
        self['exportselection'] = False

        self.focus_force()
        self.bind("<Return>", self.on_return)
        self.bind("<Control-a>", self.select_all)
        self.bind("<Escape>", lambda *ignore: self.destroy())

    def on_return(self, event):
        self.tv.item(self.iid, values=self.get())
        self.destroy()

    def select_all(self, *ignore):
        ''' Set selection on the whole text '''
        self.selection_range(0, 'end')

        # returns 'break' to interrupt default key-bindings
        return 'break'


class MergerGuiApp:
    def __init__(self, master=None, folder_callback=None):
        self.builder = builder = pygubu.Builder()
        builder.add_resource_path(PROJECT_PATH)
        builder.add_from_file(PROJECT_UI)
        # Main widget
        self.mainwindow = builder.get_object("frame1", master)
        builder.get_object("frame1").master.geometry("1280x960")	
        self.mainwindow.winfo_toplevel().title("Data Merger")
        self.mainwindow.winfo_toplevel().iconbitmap("icon.ico")
        
        builder.connect_callbacks(self)
        self.delete_button = builder.get_object("delete_button")
        self.send_button = builder.get_object("send_button")
        self.open_config_button = builder.get_object("open_config_button")
        
        self.save_button = builder.get_object("merge_button")
        self.list_files = builder.get_object("listbox_choose")
        self.list_files.config(selectmode=tk.MULTIPLE)
        
        self.combobox = builder.get_object("dateformat")
        for key, value in start_time_str.items():
            self.combobox.insert(tk.END, key)
        self.combobox.current(0)
        self.combobox.bind("<<ComboboxSelected>>", self.combobox_clicked)
        
        self.file1 = builder.get_object("listbox_1")
        self.file1.config(selectmode=tk.MULTIPLE)
        
        self.file2 = builder.get_object("listbox_2")
        self.file2.config(selectmode=tk.MULTIPLE)
        self.file3 = builder.get_object("listbox_3")#
        self.file3.config(selectmode=tk.MULTIPLE)
        
        
        self.tview = builder.get_object("tview")
        self.tview.config(selectmode=tk.BROWSE)
        self.tview["columns"]=("#1",)
        self.tview.column("#1", width=100)
        self.tview.heading('#0', text='Key')
        self.tview.heading('#1', text='Value')
        self.tview.bind("<Double-1>", self.onDoubleClick)
        
        self.file1.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.file2.bind("<<ListboxSelect>>", self.on_listbox_select)
        self.file3.bind("<<ListboxSelect>>", self.on_listbox_select)
        
        
        self.canvas = builder.get_object("canvas")
        self.canvas.create_text(100, 100, text="Your results will be shown here", fill="gray")
        
        
        self.folder_button = builder.get_object("folder_button")

        self.data_preview_frame = builder.get_object("data_preview_frame")
        self.data_preview_table = Table(self.data_preview_frame, showtoolbar=False, showstatusbar=True)
        self.data_preview_table.show()
        self.delete_button.bind("<ButtonRelease-1>", self.on_delete_button)
        self.send_button.bind("<ButtonRelease-1>", self.send_action)
        self.open_config_button.bind("<ButtonRelease-1>", self.open_config)
        
        self.save_button.bind("<ButtonRelease-1>", self.merge)
        self.folder_button.bind("<ButtonRelease-1>", self.choose_folder)
        
        
        self.save_button.config(state=tk.DISABLED)
        
        
        
        self.folder_callback = None
    
    def on_listbox_select(self, event):
        selected_item_1 = self.file1.curselection()
        selected_item_2 = self.file2.curselection()
        selected_item_3 = self.file3.curselection()
        if event.widget == self.file1:
            file_path = self.file1.get(selected_item_1[0])
            
        elif selected_item_2:
            file_path = self.file2.get(selected_item_2[0])
            
        elif selected_item_3:
            file_path = self.file3.get(selected_item_3[0])
    
        try:            
            self.data_preview_table.importCSV(self.folder_path + "/" + file_path, sep=";")
            return 
        except Exception as e:
            print(f"Error reading CSV file: {e}")
            return None
    

    
    
    def onDoubleClick(self, event):
        ''' Executed, when a row is double-clicked. Opens 
        read-only EntryPopup above the item's column, so it is possible
        to select text '''

        # close previous popups
        # self.destroyPopups()

        # what row and column was clicked on
        rowid = self.tview.identify_row(event.y)
        column = self.tview.identify_column(event.x)

        
        if not rowid:
            return
        
        if not column == '#1':
            return
        
        # get column position info
        x,y,width,height = self.tview.bbox(rowid, "#1") 

        # y-axis offset
        # pady = height // 2
        pady = 0

        # place Entry popup properly         
        
        text = self.tview.item(rowid, 'values')
        self.entryPopup = EntryPopup(self.tview, rowid, text)
        self.entryPopup.place( x=0, y=y+pady, anchor=tk.W, relwidth=1)
        return 
        
    
    
    
        
    def run(self):
        self.mainwindow.mainloop()



    def handle_folder_selection(self, folder_path, listbox, dummy=None):
        print("Selected Folder:", folder_path)

        listbox.delete(0, tk.END)

        files = os.listdir(folder_path)
        for file in files:
            listbox.insert(tk.END, file)
            
    
    
        

    def choose_folder(self, dummy=None):
            
            #clear file 1,2,3
            
            self.file1.delete(0, tk.END)
            self.file2.delete(0, tk.END)
            self.file3.delete(0, tk.END)
            
            for i in self.tview.get_children():
                self.tview.delete(i)
        
            self.folder_path = filedialog.askdirectory()
            if self.folder_path is None or self.folder_path == '':
                return
            if self.folder_path:
                self.list_files.delete(0, tk.END)
                files = os.listdir(self.folder_path)
                for file in files:
                    self.list_files.insert(tk.END, file)
                self.handle_folder_selection(self.folder_path, self.list_files)
            self.config = None
            print(os.getcwd())
            try:
                os.chdir(os.path.dirname(__file__))
            except:
                pass
            config_fp = open("config_template.ini", "r")
            config_str = config_fp.read()
            self.config = ini.parse(config_str, on_empty_key="")
            

            
            
            
            #sections = self.config.sections()
            for section in self.config:
                self.tview.insert('', 'end', section, text=section)
                #options = self.config.options(section)
                
                for option in self.config[section]:
                    try:
                        value = self.config[section][option]
                        self.tview.insert(section, 'end', section + "_" + option, text=option, values=(value,))
                    except Exception as e:
                        print(e)
            self.update_format()
            
            block_list = []
            for child in self.tview.get_children():
                if self.tview.parent(child) in block_list:
                    section = self.tview.item(child)['text']
                    for child2 in self.tview.get_children(child):

                        option = self.tview.item(child2)['text']
                        option.replace(section + "_", "", 1)
                        if option in self.config[section]:
                           del self.config[section][option]
            
            
            #self.config.read('config_template.ini')
            self.new_value = self.folder_path + "/" + 'plot'
            #self.config.set('plot', 'plot_filename', self.new_value)
            with open('config_template.ini', 'w') as new_config_fp:
                new_config_str = ini.stringify(self.config)
                new_config_fp.write(new_config_str)
            


    def open_pdf(self, dummy=None):
        pdf_file = self.config["plot"]["plot_filename"] + ".pdf"
        
        try:
            doc = fitz.open(pdf_file)
            if doc.page_count == 0:
                # Handle the case where the PDF has no pages.
                return
            page = doc.load_page(0)
            width = page.rect.width
            height = page.rect.height
            pix = page.get_pixmap(matrix = fitz.Matrix(2, 2), dpi=150)
            

            # Use BytesIO to work with the image in memory
            img_bytes = BytesIO(pix.tobytes())
            img = Image.open(img_bytes)
            
            # Use PIL to convert the image format
            
            img = ImageTk.PhotoImage(img)
            self.canvas.create_image(0, 0,image=img, anchor=tk.NW)
            self.canvas.image = img   
            self.canvas.config(width = pix.width, height = pix.height)
        except Exception as e:
            # Handle exceptions (e.g., FileNotFoundError, fitz.errors.UnknownException)
            print(f"Error: {e}")
        
        
            
    
        
        


    
    def open_config(self, dummy=None):
        self.save_button.config(state=tk.NORMAL)
        self.config_filename = filedialog.askopenfilename()
        if self.config_filename is None or self.config_filename == '':
            return
        self.folder_path = os.path.dirname(self.config_filename)
        
        try:
            os.chdir(os.path.dirname(__file__))
        except:
            pass
        
        config_fp = open("config_template.ini", "r")
        config_str = config_fp.read()

        self.config = ini.parse(config_str,on_empty_key="")
        
        for section in self.config:
            self.tview.insert('', 'end', section, text=section)

            for option in self.config[section]:
                try:
                    self.tview.insert(section, 'end', section + "_" + option, text=option, values=(self.config[section].get(option)))
                except Exception as e:
                    print(e)

        block_list = []
        for child in self.tview.get_children():
            if self.tview.parent(child) in block_list:
                section = self.tview.item(child)['text']
                for child2 in self.tview.get_children(child):

                    option = self.tview.item(child2)['text']
                    option.replace(section + "_", "", 1)
                    if option in self.config[section]:
                        del self.config[section][option]

        


    def merge(self, dummy=None):     
        
            


            for child in self.tview.get_children():
                if self.tview.parent(child) == '':
                    section = self.tview.item(child)['text']
                    for child2 in self.tview.get_children(child):
                        option = self.tview.item(child2)['text']
                        if len(self.tview.item(child2)['values']) > 0:
                            value = str(self.tview.item(child2)['values'][0])
                            option.replace(section + "_", "", 1)
                            self.config[section][option] = str(value)        # write treeview to config file
            self.config_filename = filedialog.asksaveasfilename(initialfile = "config.ini",initialdir = self.folder_path,title = "Select file",filetypes = (("ini files","*.ini"),("all files","*.*")))
            if self.config_filename is None or self.config_filename == '':
                return
            with open(self.config_filename, 'w') as new_config_fp:
                    new_config_str = ini.stringify(self.config)
                    new_config_fp.write(new_config_str)


        
        
        
        
            if self.save_button['state'] == 'disabled':
                print("Button is disabled")
            else:
                os.chdir(self.folder_path)
                analytics.main_analytics(self.config_filename,self.folder_path)
                print("--- Merging done \u2713 ---")
                self.open_pdf()
                # open pdf_frame
        
       
        
    def combobox_clicked(self, dummy=None):
        self.update_format()
        return "break"  
        
        
    def update_format(self, dummy=None):
        combobox = self.combobox.get()
        

        

            
        if combobox is not None and combobox != "":
            self.tview.item('formats_date', values=(combobox,))
            self.tview.item('resampling_tstart', values=(start_time_str[combobox],))
            self.tview.item('resampling_tend', values=(end_time_str[combobox],))
        elif combobox == "":
            pass


    def send_action(self, dummy=None):
        
        self.save_button.config(state=tk.NORMAL)
        selected_files = self.list_files.curselection()

        if len(selected_files) == 0:
            tk.messagebox.showerror("Error", "Please select at least one _value file.")
            return
        file_paths = [self.list_files.get(index) for index in selected_files]
        

        heating_files = []
        valve_files = []
        value_files = []
       
        
        
        
        
        for file_path in file_paths:
            if file_path.lower().endswith("_heating.csv"):
                heating_files.append(file_path)
            elif file_path.lower().endswith("_valve.csv"):
                valve_files.append(file_path)
            elif file_path.lower().endswith("_values.csv"):
                value_files.append(file_path)
            elif file_path.lower().endswith(".csv"):
                value_files.append(file_path)
            else:
                tk.messagebox.showerror("Error", f"Unsupported file: {file_path}")
                return

        if len(value_files) == 0:
            tk.messagebox.showerror("Error", "Please select atleast one 'values' file.")
            return
        
        value_files, heating_files, valve_files = self.process_files(value_files, heating_files, valve_files)

        for heating_file in heating_files:
            #self.file1.delete(0, tk.END)
            self.file1.insert(0, heating_file)
        for valve_file in valve_files:
            #self.file2.delete(0, tk.END)
            self.file2.insert(0, valve_file)
        for value_file in value_files:
            #self.file3.delete(0, tk.END)
            self.file3.insert(0, value_file)
        
        self.update_filenames()
        self.process_files(self.file1.get(0, 'end'), self.file2.get(0, 'end'), self.file3.get(0, 'end'))
        return"break"
    def update_filenames(self):
        
        
        
        heating_file = ','.join(self.file1.get(0, 'end'))
        valve_file = ','.join(self.file2.get(0, 'end'))
        value_file = ','.join(self.file3.get(0, 'end'))
        self.tview.item('source_heating_csv', values=())
        self.tview.item('source_valve_csv', values=())
        self.tview.item('source_value_csv', values=())
        self.tview.item('plot_plot_filename', values=(self.file3.get(0, 'end')[0].replace("_values.csv", "")))

        # insert files into treeview
        
        if value_file:
            self.tview.item('source_value_csv', values=(value_file))
        if heating_file:
            self.tview.item('source_heating_csv', values=(heating_file))
        if valve_file:
            self.tview.item('source_valve_csv', values=(valve_file))

    def process_files(self, value_files, heating_files, valve_files):
        
        common_base_names = set()

        used_heating_files = []
        #for heating_file in heating_files:
        #    base_name_heating = os.path.splitext(heating_file)[0].lower().replace("_heating", "_values")
        #    if base_name_heating in value_files:
        #        used_heating_files.append(heating_file)
        used_heating_files = heating_files
           
        used_valve_files = []
        #for valve_file in valve_files:
        #    base_name_valve = os.path.splitext(valve_file)[0].lower().replace("_valve", "_values")
        #    if base_name_valve in value_files:
        #        used_valve_files.append(valve_file)
        used_valve_files = valve_files
        
        
        
        used_value_files = value_files


        #if not common_base_names:
        #    messagebox.showerror("Error", "No matching filenames.")
        #    return 
        return used_value_files, used_heating_files, used_valve_files


    def on_delete_button(self, dummy=None):
        selected_items_file1 = self.file1.curselection()
        selected_items_file2 = self.file2.curselection()
        selected_items_file3 = self.file3.curselection()

        for index in selected_items_file1[::-1]:
            self.file1.delete(index)

        for index in selected_items_file2[::-1]:
            self.file2.delete(index)

        for index in selected_items_file3[::-1]:
            self.file3.delete(index)


        self.update_filenames()


if __name__ == "__main__":
    root = tk.Tk()
    app = MergerGuiApp(root)
    app.run()
