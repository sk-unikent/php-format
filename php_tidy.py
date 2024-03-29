import sublime, sublime_plugin, re, os

class PhpTidyCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        FILE = self.view.file_name()
        settings = sublime.load_settings('PhpTidy.sublime-settings')

        supported_filetypes = settings.get('filetypes') or ['.php', '.module', '.inc']
        
        print('PhpTidy: invoked on file: %s' % (FILE))

        if os.path.splitext(FILE)[1] in supported_filetypes:
    
            print('PhpTidy: Ok, this seems to be PHP')            

            # set tidy type
            tidy_type = settings.get('tidytype') or 'wp'

            if tidy_type == 'wp':
                tidy_file = 'wp-phptidy.php'
            else:
                tidy_file = 'phptidy.php'

            # path to plugin - <sublime dir>/Packages/PhpTidy
            pluginpath = sublime.packages_path() + '/PhpTidy'
            scriptpath = pluginpath + '/' + tidy_file

            # path to temp file
            tmpfile = '/tmp/phptidy-sublime-buffer.php'
            phppath = '/usr/bin/php'

            # set different paths for php and temp file on windows
            if sublime.platform() == 'windows':
                tmpfile = pluginpath + '/phptidy-sublime-buffer.php'
                phppath = settings.get('php_loc')
                retval = os.system( '%s -v' % ( phppath ) )
                print('PhpTidy: calling php.exe -v returned: %s' % (retval))
                if not ((retval == 0) or (retval == 1)):
                    sublime.error_message('PhpTidy cannot find %s. Make sure it is available in your PATH. (Error %s)' % (phppath,retval))
                    return

            # set script and check if it exists
            if not os.path.exists( scriptpath ):
                sublime.error_message('PhpTidy cannot find the script at %s.' % (scriptpath))
                return

            # get current buffer
            bufferLength  = sublime.Region(0, self.view.size())
            bufferContent = self.view.substr(bufferLength).encode('utf-8')

            # write tmpfile
            fileHandle = open ( tmpfile, 'w' ) 
            fileHandle.write ( bufferContent ) 
            fileHandle.close() 
            print('PhpTidy: buffer written to tmpfile: %s' % (tmpfile))


            # call phptidy on tmpfile
            scriptpath = pluginpath + '/' + tidy_file
            print('PhpTidy: calling script: %s "%s" replace "%s"' % ( phppath, scriptpath, tmpfile ) )
            retval = os.system( '%s "%s" replace "%s"' % ( phppath, scriptpath, tmpfile ) )
            if not ((retval == 0) or (retval == 1)):
                print('PhpTidy: script returned: %s' % (retval))
                if retval == 32512:
                    sublime.error_message('PhpTidy cannot find the script at %s.' % (scriptpath))
                    return
                else:
                    sublime.error_message('There was an error calling the script at %s. Return value: %s' % (scriptpath,retval))


            # read tmpfile and delete
            fileHandle = open ( tmpfile, 'r' ) 
            newContent = fileHandle.read() 
            fileHandle.close() 
            os.remove( tmpfile )
            print('PhpTidy: tmpfile was processed and removed')

            # remove hidden tmp file generated by phptidy.php
            if os.path.exists('/tmp/.phptidy-sublime-buffer.php.phptidybak~'):
                os.remove( '/tmp/.phptidy-sublime-buffer.php.phptidybak~' )

            # write new content back to buffer
            self.view.replace(edit, bufferLength, self.fixup(newContent))


            # reminder: different ways of logging errors in sublime
            #
            # sublime.status_message('opening file: %s' % (FILE))
            # sublime.error_message(tmpfile)
            # self.show_error_panel(self.fixup(tmpfile))


    # Error panel & fixup from external command
    # https://github.com/technocoreai/SublimeExternalCommand
    def show_error_panel(self, stderr):
        panel = self.view.window().get_output_panel("php_tidy_errors")
        panel.set_read_only(False)
        edit = panel.begin_edit()
        panel.erase(edit, sublime.Region(0, panel.size()))
        panel.insert(edit, panel.size(), stderr)
        panel.set_read_only(True)
        self.view.window().run_command("show_panel", {"panel": "output.php_tidy_errors"})
        panel.end_edit(edit)

    def fixup(self, string):
        return re.sub(r'\r\n|\r', '\n', string.decode('utf-8'))
