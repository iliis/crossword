#!/bin/env python3
import npyscreen
import logging
import json

from crossword import Crossword

log = logging.getLogger('puzzle')
hdlr = logging.FileHandler('puzzle.log')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
log.addHandler(hdlr)
log.setLevel(logging.DEBUG)


class CrosswordForm(npyscreen.Form):
    def afterEditing(self):
        self.parentApp.setNextForm(None)

    def create(self):
        #self.myName        = self.add(npyscreen.TitleText, name='Name')
       #self.myDepartment = self.add(npyscreen.TitleSelectOne, scroll_exit=True, max_height=3, name='Department', values = ['Department 1', 'Department 2', 'Department 3'])
       #self.myDate        = self.add(npyscreen.TitleDateCombo, name='Date Employed')
       with open('puzzle.cfg', 'r') as puzzle_cfg:
           self.crossword = self.add(Crossword, cfg=json.load(puzzle_cfg))

class MyApplication(npyscreen.NPSAppManaged):
    def onStart(self):
        npyscreen.setTheme(npyscreen.Themes.DefaultTheme)
        self.addForm('MAIN', CrosswordForm, name='Stadtwache Ankh Morpork Management Console Login')
        # A real application might define more forms here.......

if __name__ == '__main__':

    log.info("starting application")
    with open('puzzle.cfg', 'r') as puzzle_cfg:
        cfg=json.load(puzzle_cfg)
        log.info("using configuration: {}".format(cfg))

    TestApp = MyApplication().run()
