#!/usr/bin/python3
import pathlib
import pygubu
import tkinter as tk
from tkinter import filedialog
from tkinter import messagebox
import configparser
import os
import pandas as pd
import analytics
import fitz
from PIL import Image, ImageTk  
from tkPDFViewer import tkPDFViewer as pdf



PROJECT_PATH = pathlib.Path(__file__).parent
PROJECT_UI = PROJECT_PATH / "merger_gui.ui"


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
        builder.connect_callbacks(self)
        self.delete_button = builder.get_object("delete_button")
        self.send_button = builder.get_object("send_button")
        self.open_config_button = builder.get_object("open_config_button")
        self.go_button = builder.get_object("create_config_button")
        self.save_button = builder.get_object("merge_button")
        self.list_files = builder.get_object("listbox_choose")
        self.list_files.config(selectmode=tk.MULTIPLE)
        
        
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

        
        
        
        
        self.canvas = builder.get_object("canvas")
        
        
        
        self.folder_button = builder.get_object("folder_button")
        
        self.delete_button.bind("<Button-1>", self.on_delete_button)
        self.send_button.bind("<Button-1>", self.send_action)
        self.open_config_button.bind("<Button-1>", self.open_config)
        self.go_button.bind("<Button-1>", self.perform_action)
        self.save_button.bind("<Button-1>", self.save_action)
        self.folder_button.bind("<Button-1>", self.choose_folder)
        
        
        self.folder_callback = None
    
    
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

            self.folder_path = filedialog.askdirectory()
            if self.folder_path:
                self.list_files.delete(0, tk.END)
                files = os.listdir(self.folder_path)
                for file in files:
                    self.list_files.insert(tk.END, file)
                self.handle_folder_selection(self.folder_path, self.list_files)
            self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
            self.config.read("config_template.ini")
            sections = self.config.sections()
            for section in sections:
                self.tview.insert('', 'end', section, text=section)
                options = self.config.options(section)
                for option in options:
                    try:
                        self.tview.insert(section, 'end', section+"_"+option, text=option, values=(self.config[section][option]))
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
                            self.config[section].pop(option)


    def open_pdf(self, dummy=None):
        pdf_file = self.config["plot"]["plot_filename"] + ".pdf"    
        self.pdfviewer = pdf.ShowPdf()
        self.pdfviewerWidget = self.pdfviewer.pdf_view(self.canvas, pdf_location = pdf_file, height=40, width=60)
        self.pdfviewerWidget.pack()	
    
    def perform_action(self, dummy=None):


        #self.config["source"]["heating_csv"] = heating_file
        #self.config["source"]["valve_csv"] = valve_file
        #self.config["source"]["value_csv"] = value_file
        

        for child in self.tview.get_children():
            if self.tview.parent(child) == '':
                section = self.tview.item(child)['text']
                for child2 in self.tview.get_children(child):
                    option = self.tview.item(child2)['text']
                    if len(self.tview.item(child2)['values']) > 0:
                        value = self.tview.item(child2)['values'][0]
                        option.replace(section + "_", "", 1)
                        self.config[section][option] = str(value)
        # write treeview to config file
        self.config_filename = filedialog.asksaveasfilename(initialfile = "config.ini",initialdir = self.folder_path,title = "Select file",filetypes = (("ini files","*.ini"),("all files","*.*")))
        with open(self.config_filename, 'w') as configfile:
            self.config.write(configfile)





    
    def open_config(self, dummy=None):
        self.config_filename = filedialog.askopenfilename()
        self.folder_path = os.path.dirname(self.config_filename)
        self.config = configparser.ConfigParser(interpolation=configparser.ExtendedInterpolation())
        self.config.read(self.config_filename)
        sections = self.config.sections()
        for section in sections:
            self.tview.insert('', 'end', section, text=section)
            options = self.config.options(section)
            for option in options:
                try:
                    self.tview.insert(section, 'end', section+"_"+option, text=option, values=(self.config[section][option]))
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
                        self.config[section].pop(option)



    def save_action(self, dummy=None):        
        analytics.main_analytics(self.config_filename, self.folder_path)
        #self.open_pdf()
        




    def send_action(self, dummy=None):
        selected_files = self.list_files.curselection()

        if len(selected_files) == 0:
            tk.messagebox.showerror("Error", "Please select at least one _value file.")
            return
        file_paths = [self.list_files.get(index) for index in selected_files]

        heating_file = None
        valve_file = None
        value_file = None

        for file_path in file_paths:
            if file_path.lower().endswith("_heating.csv"):
                heating_file = file_path
            elif file_path.lower().endswith("_valve.csv"):
                valve_file = file_path
            elif file_path.lower().endswith("_values.csv"):
                value_file = file_path
            else:
                tk.messagebox.showerror("Error", f"Unsupported file: {file_path}")

        if value_file is None:
            tk.messagebox.showerror("Error", "Please select atleast one 'values' file.")
            return


        if heating_file:
            #self.file1.delete(0, tk.END)
            self.file1.insert(0, heating_file)
        if valve_file:
            #self.file2.delete(0, tk.END)
            self.file2.insert(0, valve_file)
        if value_file:
            #self.file3.delete(0, tk.END)
            self.file3.insert(0, value_file)

        self.update_filenames()

    def update_filenames(self):
        heating_file = ','.join(self.file1.get(0, 'end'))
        valve_file = ','.join(self.file2.get(0, 'end'))
        value_file = ','.join(self.file3.get(0, 'end'))
        self.tview.item('source_heating_csv', values=())
        self.tview.item('source_valve_csv', values=())
        self.tview.item('source_value_csv', values=())

        # insert files into treeview
        if value_file:
            self.tview.item('source_value_csv', values=(value_file))
        if heating_file:
            self.tview.item('source_heating_csv', values=(heating_file))
        if valve_file:
            self.tview.item('source_valve_csv', values=(valve_file))

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
