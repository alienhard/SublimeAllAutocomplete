# Extends Sublime Text autocompletion to find matches in all open
# files. By default, Sublime only considers words from the current file.

import sublime_plugin
import sublime
import re
import time

from os.path import basename

# Import the debugger
from debug_tools import getLogger

# Debugger settings: 0 - disabled, 127 - enabled
log = getLogger( 1, basename( __file__ ) )

# limits to prevent bogging down the system
MAX_FIX_TIME_SECS_PER_VIEW = 0.01


def plugin_unloaded():
    g_settings.clear_on_change('All Autocomplete')


def plugin_loaded():
    on_settings_modified();
    g_settings.add_on_change('All Autocomplete', on_settings_modified)


def on_settings_modified():
    log( 2, "on_settings_modified" )

    global g_settings
    g_settings = sublime.load_settings('All Autocomplete.sublime-settings')


class AllAutocomplete(sublime_plugin.EventListener):

    def on_query_completions( self, active_view, prefix, locations ):
        # log( 16, "" )

        if is_disabled_in(active_view.scope_name(locations[0])):
            return []

        words_list       = []
        words_list_clean = []
        start_time       = time.time()

        if len( locations ) > 0:
            view_words = active_view.extract_completions( prefix, locations[0] )

        else:
            view_words = active_view.extract_completions( prefix )

        view_words = fix_truncation( active_view, view_words )

        # This view goes first to prioritize matches close to cursor position.
        for word in view_words:
            # Remove the annoying `(` on the string
            word = word.replace('$', '\\$').split('(')[0]

            if word not in words_list_clean:
                words_list.append( ( word, word ) )
                words_list_clean.append( word )

            if time.time() - start_time > 0.05:
                break

        # log( 16, "Current views loop took: %f" % ( time.time() - start_time ) )
        buffers_id_set = set()
        view_base_name = None

        views = []
        windows = sublime.windows()

        for window in windows:
            views.extend(window.views())

        buffers_id_set.add( active_view.buffer_id() )

        for view in views:
            view_buffer_id = view.buffer_id()
            # log( 16, "view: %d" % view.id() )
            # log( 16, "buffers_id: %d" % view_buffer_id )
            # log( 16, "buffers_id_set size: %d" % len( buffers_id_set ) )

            if view_buffer_id not in buffers_id_set:
                buffers_id_set.add( view_buffer_id )
                view_base_name = view.file_name()

                view_words = view.extract_completions(prefix)
                view_words = fix_truncation(view, view_words)

                if view_base_name is None:
                    view_base_name = ""

                else:
                    view_base_name = basename( view_base_name )

                for word in view_words:
                    # Remove the annoying `(` on the string
                    word = word.replace('$', '\\$').split('(')[0]

                    if word not in words_list_clean:
                        # log( 16, "word: %s" % word )
                        words_list.append( ( word + ' \t' + view_base_name, word ) )
                        words_list_clean.append( word )

                    if time.time() - start_time > 0.3:
                        # log( 16, "Breaking all views loop after: %f" % time.time() - start_time )
                        return words_list

        # log( 16, "All views loop took: %f" % ( time.time() - start_time ) )
        return words_list


def is_disabled_in(scope):
    excluded_scopes = g_settings.get("exclude_from_completion", [])

    for excluded_scope in excluded_scopes:

        if scope.find(excluded_scope) != -1:
            return True

    return False


# Ugly workaround for truncation bug in Sublime when using view.extract_completions()
# in some types of files.
def fix_truncation(view, words):
    fixed_words = []
    start_time = time.time()

    for i, w in enumerate(words):
        #The word is truncated if and only if it cannot be found with a word boundary before and after

        # this fails to match strings with trailing non-alpha chars, like
        # 'foo?' or 'bar!', which are common for instance in Ruby.
        match = view.find(r'\b' + re.escape(w) + r'\b', 0)
        truncated = is_empty_match(match)

        if truncated:
            #Truncation is always by a single character, so we extend the word by one word character before a word boundary
            extended_words = []
            view.find_all(r'\b' + re.escape(w) + r'\w\b', 0, "$0", extended_words)

            if len(extended_words) > 0:
                fixed_words += extended_words

            else:
                # to compensate for the missing match problem mentioned above, just
                # use the old word if we didn't find any extended matches
                fixed_words.append(w)
        else:
            #Pass through non-truncated words
            fixed_words.append(w)

        # if too much time is spent in here, bail out,
        # and don't bother fixing the remaining words
        if time.time() - start_time > MAX_FIX_TIME_SECS_PER_VIEW:
            return fixed_words + words[i+1:]

    return fixed_words


if sublime.version() >= '3000':

    def is_empty_match(match):
        return match.empty()

else:
    plugin_loaded()

    def is_empty_match(match):
        return match is None

