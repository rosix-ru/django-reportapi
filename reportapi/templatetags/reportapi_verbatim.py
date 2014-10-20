# -*- coding: utf-8 -*-
#
#  reportapi/templatetags/reportapi_verbatim.py
#  
#  Copyright 2014 Grigoriy Kramarenko <root@rosix.ru>
#  
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 3 of the License, or
#  (at your option) any later version.
#  
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#  
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#  
#  
"""
jQuery templates use constructs like:

    {{if condition}} print something{{/if}}

This, of course, completely screws up Django templates,
because Django thinks {{ and }} mean something.

Wrap {% verbatim %} and {% endverbatim %} around those
blocks of jQuery templates and this will try its best
to output the contents with no changes.
"""

from django import template

register = template.Library()

class VerbatimNode(template.Node):

    def __init__(self, text):
        self.text = text
    
    def render(self, context):
        return self.text

@register.tag
def verbatim(parser, token):
    text = []
    while 1:
        token = parser.tokens.pop(0)
        if token.contents == 'endverbatim':
            break
        if token.token_type == template.TOKEN_VAR:
            text.append(template.VARIABLE_TAG_START)
        elif token.token_type == template.TOKEN_BLOCK:
            text.append(template.BLOCK_TAG_START)
        elif token.token_type == template.TOKEN_COMMENT:
            text.append(template.COMMENT_TAG_START)
        text.append(token.contents)
        if token.token_type == template.TOKEN_VAR:
            text.append(template.VARIABLE_TAG_END)
        elif token.token_type == template.TOKEN_BLOCK:
            text.append(template.BLOCK_TAG_END)
        elif token.token_type == template.TOKEN_COMMENT:
            text.append(template.COMMENT_TAG_END)
    return VerbatimNode(''.join(text))
