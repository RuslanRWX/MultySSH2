#!/usr/bin/python
# MultySSH2  version 2.0
# Copytight (c) Ruslan Variushkin, ruslan@host4.biz
# python version 2.x,3.5,3.6,3.7
# recommend python version 3.7

import urwid
import sys
import re
import io
import getpass
import argparse
import json
import os

ansible_file="/etc/ansible/hosts"
cat_hosts_file = open(ansible_file).readlines()
Host=None


def put_key(key):
    if key in ('q', 'Q'):
        raise urwid.ExitMainLoop()

def fetch_line():
    for lines in cat_hosts_file:
        line = lines.split()
        if len(line) > 0 and re.match( "^#", line[0]) is None:
            yield line


def command(host):
    host = str(host).replace("[", "").replace("'","").replace("]","")
    for lines in cat_hosts_file:
        line = lines.split()
        if len(line) > 0 and re.match( "^#", line[0]) is None :
            if re.search(host, line[0]):
                ip=line[1].strip().replace("ansible_ssh_host=","")
                port = line[2].strip().replace("ansible_ssh_port=", "")
                return "ssh -p{port} root@{ip}".format(port=port,ip=ip)


def connect_ssh(host):
    cmd=command(host)
    os.system(cmd)


def groups():
    groups=set()
    for group in fetch_line():
        if re.match("^\[", group[0]):
            group = group[0].strip("[]")
            groups.add(group)
    return groups


def hosts(group):
    flag=0
    lines=[]
    notcheck = False
    pattern = "^\["+group+"\]"
    for line in fetch_line():
        if notcheck == 1 and re.match("^\[", line[0]):
            break
        if re.match(pattern, line[0]):
            flag = 1
            notcheck = 1
        if flag == 1:
            if re.match(pattern, line[0]) is None:
                lines.append(line[:1])
    return lines


def menu_hosts(group):
    for host in hosts(group):
        yield Choice(host)


def menu_groups():
    for group in groups():
        yield SubMenu(group, [x for x in menu_hosts(group)])


def menu_main():
    return SubMenu(u'Groups', [ x for x in menu_groups() ])


class MenuButton(urwid.Button):
    def __init__(self, caption, callback):
        super(MenuButton, self).__init__("")
        urwid.connect_signal(self, 'click', callback)
        self._w = urwid.AttrMap(urwid.SelectableIcon(
            [u'  \N{BULLET} ', caption], 2), None, 'selected')


class SubMenu(urwid.WidgetWrap):
    def __init__(self, caption, choices):
        super(SubMenu, self).__init__(MenuButton(
            [caption, u"\N{HORIZONTAL ELLIPSIS}"], self.open_menu))
        line = urwid.Divider(u'\N{LOWER ONE QUARTER BLOCK}')
        listbox = urwid.ListBox(urwid.SimpleFocusListWalker([
            urwid.AttrMap(urwid.Text([u"\n  ", caption]), 'heading'),
            urwid.AttrMap(line, 'line'),
            urwid.Divider()] + choices + [urwid.Divider()]))
        self.menu = urwid.AttrMap(listbox, 'options')

    def open_menu(self, button):
        top.open_box(self.menu)


class Choice(urwid.WidgetWrap):
    def __init__(self, caption):
        super(Choice, self).__init__(
            MenuButton(caption, self.item_chosen))
        self.caption = caption

    def item_chosen(self, button):
        response = urwid.Text([u'  You chose ', self.caption, u'\n'])
        done = MenuButton(u'Ok', self.select_program)
        response_box = urwid.Filler(urwid.Pile([response, done]))
        top.open_box(urwid.AttrMap(response_box, 'options'))

    def select_program(self, button):
        global Host
        Host = self.caption
        raise urwid.ExitMainLoop()


def exit_program(key):
    raise  urwid.ExitMainLoop()

palette = [
    (None,  'light gray', 'black'),
    ('heading', 'black', 'light gray'),
    ('line', 'black', 'light gray'),
    ('options', 'dark gray', 'black'),
    ('focus heading', 'white', 'dark red'),
    ('focus line', 'black', 'dark red'),
    ('focus options', 'black', 'light gray'),
    ('selected', 'white', 'dark blue')]
focus_map = {
    'heading': 'focus heading',
    'options': 'focus options',
    'line': 'focus line'}


class HorizontalBoxes(urwid.Columns):
    def __init__(self):
        super(HorizontalBoxes, self).__init__([], dividechars=1)

    def open_box(self, box):
        if self.contents:
            del self.contents[self.focus_position + 1:]
        self.contents.append((urwid.AttrMap(box, 'options', focus_map),
            self.options('given', 50)))
        self.focus_position = len(self.contents) - 1


if __name__ == '__main__':
    top = HorizontalBoxes()
    top.open_box(menu_main().menu)
    urwid.MainLoop(urwid.Filler(top, 'top', 30), palette, unhandled_input=put_key).run()
    if Host:
        connect_ssh(Host)
    exit (0)
