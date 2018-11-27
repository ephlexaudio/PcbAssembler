#!/usr/bin/python

import os
import sys
import Tkinter
from Tkinter import *
import tkMessageBox
from PIL import Image, ImageTk
import getopt
import tkFileDialog
import csv


offset = {'x':0,'y':0} # position of lower left corner of PCB image on canvas
fab_file_lines = [] # lines from Fabmaster file
pcb_dimensions = {'x':400,'y':600}  # size of canvas
component_markers = [] # list of component locations for selected component value
bom_line = {'quant':0,'value':'','pack':'','part_names':[]}
bom_lines = [] # lines from CSV file
top = Tkinter.Tk()
bom_list_box = Listbox(top, height=100, selectmode=SINGLE) #first list box (component values)
part_name_list_box = Listbox(top, height=100, selectmode=SINGLE) #second list box (part names for components of same value)
Pcb = Tkinter.Canvas(top)
top.title("PCB Assembler")


def get_fab_file_data(filename_root):
    fab_file = open(filename_root+".fab",'r')
    fab_file_data = fab_file.readlines()
    for line in fab_file_data:
        fab_file_lines.append(line)

def get_pcb_dimensions():
    pcb_dim = {}
    parse_line = ""
    for line in fab_file_lines:
        if line.find("WORK_SPACE") >= 0:
            parse_line = line.split('(')[1]
            parse_line = parse_line.translate(None, ''.join([';',')']))
            dimensions = parse_line.split(',')
            if int(dimensions[0])/10 != 0:
                offset['x'] = -int(dimensions[0])/10
            if int(dimensions[2])/10 != 0:
                offset['y'] = -int(dimensions[2])/10
            pcb_dim['x'] = int(dimensions[1])/10-int(dimensions[0])/10
            pcb_dim['y'] = int(dimensions[3])/10-int(dimensions[2])/10

    return pcb_dim


def get_pcb_data():
    global display #this needs to be global for PCB image to show

    # Dialog box for selecting PCB image file
    ftypes = [('GIF', '*.gif')]
    dlg = tkFileDialog.Open(filetypes = ftypes,initialdir = dir)
    image = dlg.show()
    pcb_root_name = image.split('.')[0]

    get_fab_file_data(pcb_root_name)
    pcb_dimensions = get_pcb_dimensions()
    pcb_image = Image.open(image)
    pcb_image = pcb_image.resize((pcb_dimensions['x'],pcb_dimensions['y']), Image.ANTIALIAS)
    width,height=pcb_image.size

    yscrollbar = Scrollbar(top)
    Pcb.config(bg="white", height=pcb_dimensions['y'], width=pcb_dimensions['x'],
                             yscrollcommand=yscrollbar.set, scrollregion=(0,0,width,height))
    yscrollbar.pack( side = RIGHT, fill=Y )
    yscrollbar.config( command = Pcb.yview )
    display = ImageTk.PhotoImage(pcb_image)
    Pcb.create_image(0,0,image=display,anchor = NW)
    Pcb.pack(side=LEFT)

def get_bom_data():
    ftypes = [('CSV', '*.csv')]

    # Dialog box for selecting BOM (Bill Of Materials) file
    dlg = tkFileDialog.Open(filetypes = ftypes,initialdir = dir)
    csv_file_path_name_string = dlg.show()

    # transfer csv file data into bom_lines dictionary list
    with open(csv_file_path_name_string, 'r') as csvfile:
        csvreader = csv.reader(csvfile, delimiter=',')
        header = csvreader.next()
        quant_col = header.index("Qty")
        value_col = header.index("Value")
        pack_col = header.index("Package")
        part_names_col = header.index("Parts")
        for row in csvreader:
            bom_line = {'quant':0,'value':'','pack':'','part_names':[]}
            bom_line['quant'] = row[quant_col]
            bom_line['value'] = row[value_col]
            bom_line['pack'] = row[pack_col]
            bom_line['part_names'] = row[part_names_col].replace(" ","").split(',')
            bom_list_box.insert(END, bom_line['value'])
            bom_lines.append(bom_line)

def get_component_locations(): # from Fabmaster file data
    parts_section = False
    component_locations = {}
    for line in fab_file_lines:
        if line.find("PARTS") >= 0:
            parts_section = True
        elif line.find(":EOD") >= 0:
            parts_section = False

        elif parts_section:
            comp_loc = {"x":0,"y":0,"side":""}
            parse_line = line.split(',')
            comp_loc['x'] = int(parse_line[4])/10+offset['x']
            comp_loc['y'] = int(parse_line[5])/10+offset['y']
            comp_loc['side'] = parse_line[7].replace(";","")
            component_locations[parse_line[1]] = comp_loc
    return component_locations

def get_parts(evt):
    global component_markers
    pcb_dimensions = get_pcb_dimensions()
    component_locations = get_component_locations()

    # clear PCB image of any previous markers
    parts = []
    for mark in component_markers:
        Pcb.delete(mark)
    component_markers = []

    #get index of part clicked on in component values list box
    part_index = map(int, bom_list_box.curselection())[0]

    part_array = bom_lines[part_index]['part_names']
    part_name_list = []
    parts = part_array
    # clear part name list box
    part_name_list_box.delete(0, END)

    # list part names in list box
    for part in parts:
        part = part.upper()
        part_name_list_box.insert(END, part)
        if component_locations[part]['side'].find('T') >= 0:
            color = "red"
        else:
            color = "blue"
        coord = {'x': component_locations[part]['x'],'y':pcb_dimensions['y'] - component_locations[part]['y']}
        circle = Pcb.create_arc([coord['x']-8,
                                 coord['y']-8,
                                 coord['x']+8,
                                 coord['y']+8],
                                start = 0, extent = 358, outline = color, width = 3)
        Pcb.pack(side=LEFT)
        component_markers.append(circle)

def main(argv):
    global bom_list_box
    global pcb_dimensions

    menubar = Menu(top)
    filemenu = Menu(menubar, tearoff=0)
    filemenu.add_command(label="Get PCB Data", command=get_pcb_data)
    filemenu.add_command(label="Get BOM Data", command=get_bom_data)
    menubar.add_cascade(label="File", menu=filemenu)
    top.config(menu=menubar)

    bom_list_box.pack(side=LEFT)
    bom_list_box.bind('<<ListboxSelect>>', get_parts)

    part_name_list_box.pack(side=LEFT)

    top.mainloop()

if __name__ == "__main__":
   main(sys.argv[1:])
