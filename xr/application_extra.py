# -*- coding: utf-8 -*-
#
import cgi
import datetime
import logging
import urllib
import time
import re
import random

from django import forms, template
from django.conf import settings
from django.core.urlresolvers import reverse
from django.template import Node, NodeList, VariableDoesNotExist, TemplateSyntaxError, resolve_variable
from django.template.base import TagHelperNode
from django.template.loader import render_to_string, get_template
from django.template.defaultfilters import stringfilter
from django.template.defaultfilters import linebreaksbr, mark_safe
# from django.template.defaulttags import TemplateIfParser #TemplateLiteral,
from django.utils.encoding import smart_unicode
from django.template import RequestContext, Context
# from submodule.mobilejp import emoji
# from submodule.gsocial.templatetags.osmobile import opensocial_url_convert, url_to_opensocial_url
from gsocial.templatetags.osmobile import opensocial_url_convert
# from submodule.gsocial.containerdata import containerdata
from module.misc.datetime_util import DatetimeUtil
from module import i18n as T
from module.common import text_spacer
from module.common.deviceenvironment.device_environment import media_url # , media_root
from common.deviceenvironment.device_environment import is_smartphone
# from module.element.api import get_element_all
# from module.guide.api import get_guide_message
# from module.misc.api_utils import is_digits
from module.item import api as item_api

from module.playeritem.api import get_player_item_from_item
# from module.playercard.models import PlayerCard
from player import extends
extends

from module.card.api import get_dummy_card

from templatetags.common_extra import url_to_opensocial_url_switcher, opensocial_url_convert_switcher
from website.css.fp import css # ←template_tagsでfp用のcssを呼ぶのはオカシイ!

from module.common.navi import Navi
from eventmodule import Event
from module.campaign.api import get_active_buildup_campaign
from module.playercard.models import PlayerCard
from module.card.models import Card, CardDetail
from module.card.api import get_card


SPACER_URL = u'%s/imgs/common/spacer.gif' % media_url()

register = template.Library()

# 追加のテンプレートタグを記述する

@register.filter
def date_to_string(date_object, date_format=u'%Y/%m/%d'):
    if date_object:
        return smart_unicode(date_object.strftime(date_format))

    return u''

@register.simple_tag
def log(message):
    logging.debug(message)
    return u''


@register.filter(name='nbsp')
@stringfilter
def nbsp(value):
    return mark_safe(value.replace(' ', '&nbsp;'))

@register.simple_tag
def guide_name(player):
    return T.GUIDE_NAME

@register.simple_tag
def guide_image_medium(player=None, width=60, height=60, filename='1.gif'):
    '''
    ガイド表示
    '''
    #if player.is_male():
    #    filename = '2.gif'
    #else:
    #    filename = '1.gif'
    filename = '%s' % (filename) #ヒーローでは、プレイヤー性別にかかわらず1.gif
    html = u'<img src="%s/imgs/navi/medium/%s" width="%d" height="%d" />' % (media_url(), filename, width, height)
    return html

@register.simple_tag
def guide_image_large(player, width=90, height=90, filename='1.gif'):
    '''
    ガイド表示
    '''
    #if player.is_male():
    #    filename = '2.gif'
    #else:
    #    filename = '1.gif'
    filename = '%s' % (filename) #ヒーローでは、プレイヤー性別にかかわらず1.gif
    html = u'<img src="%s/imgs/navi/large/%s" width="%d" height="%d" />' % (media_url(), filename, width, height)
    return html

@register.simple_tag(takes_context=True)
def player_detail(context, player):
    '''
    プレイヤー表記
    '''
    prof_href = url_to_opensocial_url_switcher(reverse('mobile_root_profile', args=[player.pk]), context)
    html = u'<a href="%s">%s</a><br />' % (prof_href, player.name)
    html += u'<span class="param_value">%s</span><br />' % player.team.name
    html += u'<table class="table_full"><tr>'
    html += u'<td class="td_thumbnail"><img src="%s" class="image_card_small" /></td>' % (player.leader_player_card_image_url()['small'])
    html += u'<td class="td_thumbnail"><img src="%s" class="player_thumbnail" /></td>' % (player.thumbnail_url)
#    html += u'<td><div class="left">%s<br />' % (player.name,)
    html += u'<td><div class="left"><span class="param_name">%s</span>:<span class="param_value">%d</span><br />' % (text_spacer.justifynbsp(T.LEVEL, 6), player.level,)
    html += u'<span class="param_name">%s</span>:<span class="param_value">%d%s</span></div></td>' % (text_spacer.justifynbsp(T.CARD, 6), player.card_count, T.CARD_COUNT)
    html += u'</tr></table>'

    return html

@register.simple_tag
def progress_bar_blue(max, original, fluctuate=0):
    return progress_bar(max, original, fluctuate, 'blue')

@register.simple_tag
def progress_bar_silver(max, original, fluctuate=0):
    return progress_bar(max, original, fluctuate, 'silver')

@register.simple_tag
def progress_bar_purple(max, original, fluctuate=0):
    return progress_bar(max, original, fluctuate, 'silver')

@register.simple_tag
def progress_bar_blue_short(max, original, fluctuate=0):
    return progress_bar(max, original, fluctuate, 'blue', progress_width=40)

@register.simple_tag
def progress_bar_silver_short(max, original, fluctuate=0):
    return progress_bar(max, original, fluctuate, 'silver', progress_width=40)

@register.simple_tag
def progress_bar_purple_short(max, original, fluctuate=0):
    return progress_bar(max, original, fluctuate, 'silver', progress_width=40)


@register.simple_tag
def progress_bar(max, original, fluctuate=0, color='progress', progress_width=60):
    '''
    original = 元の値
    fluctuage = 増減値
    '''
    PROGRESS_IMG = u'<img class="progress-image-%s" src="%s/imgs/gauge/%s.gif" width="%d" height="12" />'
    max = float(max) if max else 0.0
    original = int(original) if original else 0
    fluctuate = float(fluctuate)
    green_width = yellow_width = red_width = 0
    # 割合を求める
    if max is None or max == 0:
        max = 1

    #限界突破してしまう対応
    if max < original:
        original = max
    if max < (original + fluctuate):
        fluctuate = max - original

    if fluctuate >= 0:
        yellow_width = int(progress_width * (float(original) / max))
        green_width = int(progress_width * (float(fluctuate) / max))
    elif fluctuate < 0:
        yellow_width = int(progress_width * ((float(original) + fluctuate) / max))
        red_width = int(progress_width * (float(-fluctuate) / max))
    else:
        raise

    black_width = progress_width - green_width - yellow_width - red_width

    start = "{}_start".format(color)
    end = "{}_end".format(color)
    progress_tag = u''
    progress_tag += PROGRESS_IMG % ('start', media_url(), start, 12)
    if yellow_width > 0:
        progress_tag += PROGRESS_IMG % ('progress', media_url(), color, yellow_width)
    if green_width > 0:
        progress_tag += PROGRESS_IMG % ('flunc', media_url(), 'flunc', green_width)
    if red_width > 0:
        progress_tag += PROGRESS_IMG % ('flunc', media_url(), 'flunc', red_width)
    if black_width > 0:
        progress_tag += PROGRESS_IMG % ('rest', media_url(), 'rest', black_width)

    #progress_tag += PROGRESS_IMG % (media_url(), 'black', 100)
    progress_tag += PROGRESS_IMG % ('end', media_url(), end, 12)

    # print progress_tag
    return progress_tag


# spacer ----

@register.simple_tag
def spacer(height=1):
    """結局、Docomoの古携帯用にspacerは必要...か"""
    return '<img src="%s" height="1" width="1" style="margin-top:%spx;display:block;" />' % (SPACER_URL, height-1)

@register.simple_tag
def spacer_br(height=1):
    return '<img src="%s" height="1" width="1" style="margin-top:%spx" /><br />' % (SPACER_URL, height-1)


# hr ----
HTML_HR = u'''<hr size="%(HEIGHT)s" style="color:%(COLOR)s;background-color:%(COLOR)s;height:%(HEIGHT)spx;border:0px solid %(COLOR)s;margin:%(MARGIN)spx 0;"  />'''
#HTML_HR = u'''<hr size="%(HEIGHT)s" style="width:100%%;height:%(HEIGHT)spx;margin:%(MARGIN)spx 0;padding:0;color:%(COLOR)s;background:%(COLOR)s;border:%(HEIGHT)spx solid %(COLOR)s;" />'''

#Docomo用の、hrの代わりのdiv
HTML_HR_DIV = u'''<div style="background-color:%(COLOR)s;"><img src="{}" height="%(HEIGHT)s" width="1" style="display:block;" /></div>'''.format(SPACER_URL)

def _is_docomo(context, default=True):
    """
    hr や section_header で、docomo端末用かそれ以外かを判断
    ※docomo端末は <div> で、それ以外は <hr> で水平線を出す。
    デフォルト状態は、docomo用の<div>で出したほうが安全かも。
    (auだと下にスキマが開く)
    """
    if not context:
        return default
    device = context.get('device', None)
    if not device:
        request = context.get('request', None)
        if request:
            device = request.get('device', None)
    if device:
        return device.is_docomo()
    else:
        return default

def _is_softbank(context, default=True):
    """
    hr_imgの時AUとDOCOMOは線の上に隙間が入るけど,softbankは入らないから分ける
    """
    if not context:
        return default
    device = context.get('device', None)
    if not device:
        request = context.get('request', None)
        if request:
            device = request.get('device', None)
    if device:
        return device.is_softbank()
    else:
        return default

@register.simple_tag(takes_context=True)
def hr_spacer(context=None, height=8, color='#333333', margin=0):
    #return u'<hr size="%d" style="width:240px;height:%dpx;margin:0;padding:0;color:%s;background:%s;border-top:%dpx solid %s;" />' % (height, height, color, color, height, color)
    return hr(context, color, height, margin)
    #return HTML_HR % {'HEIGHT': height, 'COLOR': color, 'MARGIN': margin,}


@register.simple_tag(takes_context=True)
def hr(context=None, color=css.HR_COLOR['default'], height=1, margin=2):
    if _is_docomo(context):
        return HTML_HR_DIV % {'HEIGHT': height, 'COLOR': color,}
    else:
        return HTML_HR % {'HEIGHT': height, 'COLOR': color, 'MARGIN': margin,}

@register.simple_tag(takes_context=True)
def hr_class(context, cls, height=1, margin=0):
    color = css.HR_COLOR.get(cls, u'#000000')
    return hr(context, color, height, margin)

@register.simple_tag(takes_context=True)
def hr_spacer_class(context, cls, height=8, margin=0):
    """
    colored_block の中でスペーサーする時など
    """
    color = css.HR_COLOR.get(cls, u'#000000');
    return hr(context, color, height, margin)

@register.simple_tag(takes_context=True)
def hr_img(context=None):
    """
    水平線画像を描画。主にリストとかで使う
    """
    html  = u'<div style="margin-top:2px;margin-bottom:2px;">'
    html += u'<img src="%s/imgs/common/hr.gif" style="width:240px;height:1px;" />' % media_url()
    html += u'</div>'
    return html

@register.simple_tag(takes_context=True)
def no_spacer_hr_img(context=None):
    """
    水平線画像を描画。主にheader上下に使う
    """
    if _is_softbank(context):
        html = u'<img src="%s/imgs/common/hr.gif" style="width:240px;height:1px;" />' % media_url()
    else:
        html  = u'<div style="margin-top:-8px;margin-bottom:-2px;">'
        html += u'<img src="%s/imgs/common/hr.gif" style="width:240px;height:1px;" />' % media_url()
        html += u'</div>'
    return html


@register.simple_tag
def hr_img_tb():
    """
    上にぼけ足のある水平線画像
    """
    html = u'<img src="%s/imgs/common/hr_tb.gif" style="width:240px;height:7px;" />' % media_url()
    return html

@register.simple_tag
def hr_img_bb():
    """
    下にぼけ足のある水平線画像
    """
    html = u'<img src="%s/imgs/common/hr_bb.gif" style="width:240px;height:6px;" />' % media_url()
    return html

# section_header 標準 ----
def _section_header_hr_top_docomo():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

# section_header 標準 ----
def _section_header_hr_top_docomo_new():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

def _section_header_hr_img():
    html = no_spacer_hr_img()
    return html

def _section_header_hr_bottom_docomo():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

def _section_header_hr_top():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

def _section_header_hr_top_new():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

def _section_header_hr_bottom():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

def _section_header_hr_bottom_new():
    html = u'<div>%s'  % sub_header_img() + u'</div>'
    return html

def _section_header(context, div_class='section_header'):
    if _is_docomo(context):
        html  = _section_header_hr_top_docomo()
        html += u'<div class="%s">' % div_class
        return html
    else:
        html  = _section_header_hr_top()
        html  += u'<div class="%s">' % div_class
        return html

def _section_header_new(context, div_class='section_header_4'):
    if _is_docomo(context):
        html  = _section_header_hr_img()
        html += u'<div class="%s">' % div_class
        html += hr_spacer(context,4,'#000000')
        return html
    else:
        html  = _section_header_hr_img()
        html  += u'<div class="%s">' % div_class
        html += hr_spacer(context,4,'#000000')
        return html

def _end_section_header_new(context):
    if _is_docomo(context):
        html = hr_spacer(context,4,'#000000')
        html  += u'</div>'
        html += _section_header_hr_img()
        return html
    else:
        html = hr_spacer(context,4,'#000000')
        html += u'</div>'
        html  += _section_header_hr_img()
        return html

def _end_section_header(context):
    if _is_docomo(context):
        html  = u'</div>'
        html += _section_header_hr_bottom_docomo()
        return html
    else:
        html = u'</div>'
        html  += _section_header_hr_bottom()
        return html



@register.simple_tag(takes_context=True)
def section_header(context, div_class='section_header'):
    """
    汎用飾りヘッダ
    """
    return _section_header(context, div_class=div_class)

@register.simple_tag(takes_context=True)
def gashapon_normal_section_header(context):
    """
    ガシャポン用ヘッダー
    """
    return _section_header(context, div_class='gashapon_normal_section_header')

@register.simple_tag(takes_context=True)
def gashapon_golden_section_header(context):
    """
    ガシャポン用ヘッダー
    """
    return _section_header(context, div_class='gashapon_golden_section_header')

@register.simple_tag(takes_context=True)
def gashapon_fukubukuro_section_header(context):
    """
    ガシャポン用ヘッダー
    """
    return _section_header(context, div_class='gashapon_fukubukuro_section_header')

@register.simple_tag(takes_context=True)
def gashapon_ticket_section_header(context):
    """
    ガシャポン用ヘッダー
    """
    return _section_header(context, div_class='gashapon_ticket_section_header')


@register.simple_tag(takes_context=True)
def battle_result_section_header(context):
    """
    試合結果用ヘッダー
    """
    return _section_header(context, div_class='battle_result_section_header')

@register.simple_tag(takes_context=True)
def battle_order_section_header(context):
    """
    試合結果用ヘッダー
    """
    return _section_header(context, div_class='battle_order_section_header')

@register.simple_tag(takes_context=True)
def section_header_menu(context, div_class='section_header_menu'):
    """
    汎用飾りヘッダ
    """
    return _section_header(context, div_class)

@register.simple_tag(takes_context=True)
def section_header_menu_new(context):
    """
    汎用飾りヘッダ(TOPページとか視察ページ)
    """
    return _section_header_new(context, div_class='section_header_menu')

@register.simple_tag(takes_context=True)
def section_header_menu_left_new(context):
    """
    汎用飾りヘッダ
    """
    return _section_header_new(context, div_class='quest_area_info_left')

@register.simple_tag(takes_context=True)
def section_header_left(context):
    """
    汎用飾りヘッダ
    """
    return _section_header(context, div_class='section_header_left')

#クエストで使ってる
@register.simple_tag(takes_context=True)
def section_header_center(context,  div_class='section_header_center'):
    """
    汎用飾りヘッダ
    """
    return _section_header(context, div_class)
#クエストで使ってる
@register.simple_tag(takes_context=True)
def section_content_left(context):
    """
    汎用飾りコンテンツ
    """
    return _section_header(context, div_class='quest_area_info_left')

@register.simple_tag(takes_context=True)
def section_header_info(context):
    """
    汎用飾りヘッダ
    """
    return _section_header(context, div_class='section_header_info')


@register.simple_tag(takes_context=True)
def end_section_header(context):
    """
    汎用飾りヘッダ閉じる
    """
    return _end_section_header(context)

@register.simple_tag(takes_context=True)
def end_section_header_new(context):
    """
    汎用飾りヘッダ閉じる
    """
    return _end_section_header_new(context)

# section_header 特殊 ----

@register.simple_tag(takes_context=True)
def section_campaign_header(context):
    return _section_header(context, div_class='section_campaign_header')

@register.simple_tag(takes_context=True)
def section_campaign_red(context):
    return _section_header(context, div_class='section_campaign_red')

@register.simple_tag(takes_context=True)
def section_campaign_blue(context):
    return _section_header(context, div_class='section_campaign_blue')

@register.simple_tag(takes_context=True)
def section_campaign_green(context):
    return _section_header(context, div_class='section_campaign_green')

@register.simple_tag(takes_context=True)
def end_section_campaign_header(context):
    return _end_section_header(context)

@register.simple_tag(takes_context=True)
def end_section_campaign_red(context):
    return _end_section_header(context)

@register.simple_tag(takes_context=True)
def end_section_campaign_blue(context):
    return _end_section_header(context)

@register.simple_tag(takes_context=True)
def end_section_campaign_green(context):
    return _end_section_header(context)


# header_img ----


@register.simple_tag
def header_img(image_file_name, alt_text=u''):
    image_file = '%s/imgs/common/header/%s' % (media_url(), image_file_name)
    html = '<img src="%s" alt="%s" class="image_header" /><br />' % (image_file, alt_text)
    return html

@register.simple_tag
def header_img_top(image_file_name, alt_text=u''):
    image_file = '%s/imgs/common/header-top/%s' % (media_url(), image_file_name)
    html = '<img src="%s" alt="%s" class="image_header_top" /><br />' % (image_file, alt_text)
    return html


@register.tag(name="switch")
def do_switch(parser, token):
    """
    The ``{% switch %}`` tag compares a variable against one or more values in
    ``{% case %}`` tags, and outputs the contents of the matching block.  An
    optional ``{% else %}`` tag sets off the default output if no matches
    could be found::

        {% switch result_count %}
            {% case 0 %}
                There are no search results.
            {% case 1 %}
                There is one search result.
            {% else %}
                Jackpot! Your search found {{ result_count }} results.
        {% endswitch %}

    Each ``{% case %}`` tag can take multiple values to compare the variable
    against::

        {% switch username %}
            {% case "Jim" "Bob" "Joe" %}
                Me old mate {{ username }}! How ya doin?
            {% else %}
                Hello {{ username }}
        {% endswitch %}
    """
    bits = token.contents.split()
    tag_name = bits[0]
    if len(bits) != 2:
        raise template.TemplateSyntaxError("'%s' tag requires one argument" % tag_name)
    variable = parser.compile_filter(bits[1])

    class BlockTagList(object):
        # This is a bit of a hack, as it embeds knowledge of the behaviour
        # of Parser.parse() relating to the "parse_until" argument.
        def __init__(self, *names):
            self.names = set(names)
        def __contains__(self, token_contents):
            name = token_contents.split()[0]
            return name in self.names

    # Skip over everything before the first {% case %} tag
    parser.parse(BlockTagList('case', 'endswitch'))

    cases = []
    token = parser.next_token()
    got_case = False
    got_else = False
    while token.contents != 'endswitch':
        nodelist = parser.parse(BlockTagList('case', 'else', 'endswitch'))

        if got_else:
            raise template.TemplateSyntaxError("'else' must be last tag in '%s'." % tag_name)

        contents = token.contents.split()
        token_name, token_args = contents[0], contents[1:]

        if token_name == 'case':
            tests = map(parser.compile_filter, token_args)
            case = (tests, nodelist)
            got_case = True
        else:
            # The {% else %} tag
            case = (None, nodelist)
            got_else = True
        cases.append(case)
        token = parser.next_token()

    if not got_case:
        raise template.TemplateSyntaxError("'%s' must have at least one 'case'." % tag_name)

    return SwitchNode(variable, cases)

class SwitchNode(Node):
    def __init__(self, variable, cases):
        self.variable = variable
        self.cases = cases

    def __repr__(self):
        return "<Switch node>"

    def __iter__(self):
        for tests, nodelist in self.cases:
            for node in nodelist:
                yield node

    def get_nodes_by_type(self, nodetype):
        nodes = []
        if isinstance(self, nodetype):
            nodes.append(self)
        for tests, nodelist in self.cases:
            nodes.extend(nodelist.get_nodes_by_type(nodetype))
        return nodes

    def render(self, context):
        try:
            value_missing = False
            value = self.variable.resolve(context, True)
        except VariableDoesNotExist:
            no_value = True
            value_missing = None

        for tests, nodelist in self.cases:
            if tests is None:
                return nodelist.render(context)
            elif not value_missing:
                for test in tests:
                    test_value = test.resolve(context, True)
                    if value == test_value:
                        return nodelist.render(context)
        else:
            return ""

def _token_bits_parser(parser, bits):
    '''
    テンプレートタグの余りの引数を受け取ってパース
    _create_a_tag_entity_reference_tokenizer専用というわけではなく、いろいろ使えるはず。
    '''
    args = []
    kwargs = {}
    asvar = None
    for bit in iter(bits):
        if bit == 'as':
            asvar = bits.next()
            break
        else:
            for arg in bit.split(","):
                if '=' in arg:
                    k, v = arg.split('=', 1)
                    k = k.strip()
                    kwargs[k] = parser.compile_filter(v)
                elif arg:
                    args.append(parser.compile_filter(arg))
    return args, kwargs, asvar

def _create_a_tag_entity_reference_tokenizer(parser, token):
    '''
    テンプレートタグの引数を分割。
    create_a_tag_entity_reference 用
    '''
    bits = token.split_contents()
    if len(bits) < 3:
        raise TemplateSyntaxError("'%s' takes at least one argument"
                                  " (path to a view)" % bits[0])
    linklabel = bits[1]
    viewname = bits[2]

    if len(bits) > 3:
        args, kwargs, asvar = _token_bits_parser(parser, bits[3:])
    else:
        args = []
    return linklabel, viewname, args


class ATagNodeEntityReference(Node):
    '''
    create_a_tag_entity_reference で使う。
    osmobile.URLNode と同じようなクラス。ただし、dictの引数を受け取ったりはできない。
    create_a_tag_entity_reference用
    '''
    HTML_A_TAG_ENTITY_REFERENCE = u'''&lt;a href=&quot;%(URL)s&quot;&gt;%(LABEL)s（通常携帯はこちら）&lt;/a&gt; / &lt;a href=&quot;%(URL_SP)s&quot;&gt;%(LABEL)s（ｽﾏｰﾄﾌｫﾝはこちら）&lt;/a&gt;'''

    def __init__(self, link_label, view_name, args):
        self.link_label = link_label
        self.view_name = view_name
        self.args = args

    def render(self, context):
        args = [arg.resolve(context) for arg in self.args]

        try:
            # view_nameがコンテキストに含まれる変数名ならば展開して使う
            self.link_label = resolve_variable(self.link_label, context)
            self.view_name = resolve_variable(self.view_name, context)
        except template.VariableDoesNotExist:
            pass

        base_url = reverse(self.view_name, args=args, current_app=context.current_app)

        url = 'http://%s%s?signed=1&guid=ON&t=%s' % (settings.SITE_DOMAIN_FP, base_url, int(time.time()))
        url_sp = 'http://%s%s' % (settings.SITE_DOMAIN_SP, base_url)
        if not settings.OPENSOCIAL_DEBUG:
            app_url = 'http://mgadget.gree.jp/%(app_id)s' % {"app_id":settings.APP_ID}
            url = '%s?guid=ON&url=%s' % (app_url, urllib.quote(url,''))
            app_url_sp = 'http://pf.gree.jp/%(app_id)s' % {"app_id":settings.APP_ID}
            url_sp = '%s?url=%s' % (app_url_sp, urllib.quote(url_sp,''))

        self.link_label = cgi.escape(self.link_label,True)
        return self.HTML_A_TAG_ENTITY_REFERENCE % {'URL': url, 'LABEL': self.link_label, 'URL_SP': url_sp}

@register.tag
def create_a_tag_entity_reference_new(parser, token):
    '''
    プロフィールページなどで、input type="text" の中にAタグを表示する用
    '''
    linklabel, viewname, args = _create_a_tag_entity_reference_tokenizer(parser, token)
    return ATagNodeEntityReference(linklabel, viewname, args)

@register.inclusion_tag('partial/element_link.html', takes_context=True)
def element_link(context, url, element_list, current_element_index, use_all=False, sort_key_idx=None, url_params=[]):
    args_for_all = [0] if sort_key_idx is None else [0, sort_key_idx]

    args = args_for_all + url_params

    all_element_url = url_to_opensocial_url_switcher(reverse(url, args=args), context)
    new_element_list = []
    for element in element_list:
        args = [element.pk] if sort_key_idx is None else [element.pk, sort_key_idx]
        new_args = args + url_params
        element.link = url_to_opensocial_url_switcher(reverse(url, args=new_args), context)
        new_element_list.append(element)

    return {
        'url_link': all_element_url,
        'use_all': use_all,
        'element_list': new_element_list,
        'element': current_element_index,
    }

@register.inclusion_tag('partial/pager.html', takes_context=True)
def pager(context, pager, url=None, region1=None, region2=None, region3=None, region4=None, region5=None):

    request = context['request']
    url_convert = opensocial_url_convert
    args = [region1, region2, region3, region4, region5]
    while None in args: args.remove(None)

    url_prev = None
    url_next = None
    if pager['previous_page']:
        prev_args = args[:]
        prev_args.append(pager['previous_page'])
        if url:
            url_prev = url_to_opensocial_url_switcher(reverse(url, args=prev_args), context)
        else:
            url_prev = url_convert(request.path, {'page': str(pager['previous_page'])})

    if pager['next_page']:
        next_args = args[:]
        next_args.append(pager['next_page'])
        if url:
            url_next = url_to_opensocial_url_switcher(reverse(url, args=next_args), context)
        else:
            url_next = url_convert(request.path, {'page': str(pager['next_page'])})

    return {
        'pager':pager,
        'url_prev': url_prev,
        'url_next': url_next,
        }


@register.inclusion_tag('partial/sort_select_form.html', takes_context=True)
def sort_card_select_form(context, url, sort_key_list, sort_key_idx, element=None, race_list=[], race=0, chain_flag=False, form_params=[]):
    return {
        'request': context.get('request', None),
        'next_url': url,
        'sort_key_list': sort_key_list,
        'sort_key_idx': int(sort_key_idx),
        'element': element,
        'race_list': race_list,
        'choice_race': race,
        'T': T,
        'chain_flag': chain_flag,
        'form_params': form_params,
    }


@register.inclusion_tag('partial/sort_material_select_form.html', takes_context=True)
def sort_material_select_form(context, url, sort_key_list, sort_key_idx, form_params=[]):
    return {
        'request': context.get('request', None),
        'next_url': url,
        'sort_key_list': sort_key_list,
        'sort_key_idx': int(sort_key_idx),
        'T': T,
        'form_params': form_params,
    }


@register.simple_tag(takes_context=True)
def pager_sp(context, pager, url, region1=None, region2=None, region3=None, region4=None, region5=None):
    args = []

    if region1 != None:
        args.append(region1)
    if region2 != None:
        args.append(region2)
    if region3 != None:
        args.append(region3)
    if region4 != None:
        args.append(region4)
    if region5 != None:
        args.append(region5)

    previous_link = None
    if pager['previous_page']:
        previous_link = url_to_opensocial_url_switcher(reverse(url, args=args + [pager['previous_page']]), context)

    next_link = None
    if pager['next_page']:
        next_link = url_to_opensocial_url_switcher(reverse(url, args=args + [pager['next_page']]), context)

    html = u'<div class="pager">'
    if previous_link:
        html += u'<a class="button prev" href="%s" >前へ</a>' % previous_link
    else:
        html += u'<span class="button disabled prev">前へ</span>'

    if pager['last_page'] >= 1:
        html += u'&nbsp;&nbsp;[%d&nbsp;/&nbsp;%d]&nbsp;&nbsp;' % (pager['current_page'], pager['last_page'])
    else:
        html += u'<span class="disabled">&nbsp;&nbsp;[%d&nbsp;/&nbsp;1]&nbsp;&nbsp;</span>' % pager['current_page']

    if next_link:
        html += u'<a class="button next" href="%s" >次へ</a>' % next_link
    else:
        html += u'<span class="button next disabled">次へ</span>'

    html += u'</div>'

    return mark_safe(html)



@register.simple_tag(takes_context=True)
def istyle(context, istyle_id, with_style=True):
    '''
    デフォルト入力モードを指定する
    istyle_id : 3=英数 4=数字(auでは数字のみ)
    <input type="text" name="hoge" {% istyle request '3' %} /> … デフォルト英数の入力モード
    <input type="text" name="hoge" {% istyle request '4' %} /> … デフォルト数字の入力モード

    docomoの場合は、i-XHTML なので、styleに指定がいるっぽい。どうしよう。
    'style':'-wap-input-format:&quot;*&lt;ja:n&gt;&quot;;'
    ⇒styleだけは別に書く?
    '''
    istyle_id = int(istyle_id)
    device=context.get('device')
    if device.is_docomo():
        output_string =  u'''istyle="%s"''' % istyle_id
        if with_style:
            if istyle_id == 3:
                output_string += u''' style="-wap-input-format:&quot;*&lt;ja:en&gt;&quot;"'''
            elif istyle_id == 4:
                output_string += u''' style="-wap-input-format:&quot;*&lt;ja:n&gt;&quot;;"'''
        return output_string
    elif device.is_ezweb(): #dictにすべきか？
        if istyle_id == 3:
            return u'''format="*m"'''
        elif istyle_id == 4:
            return u'''format="*N"'''
    elif device.is_softbank(): #dictにすべきか？
        if istyle_id == 3:
            return u'''mode="alphabet"'''
        elif istyle_id == 4:
            return u'''mode="numeric"'''
    return u''


@register.filter
def get_percent(curent_value, max_value):
    """
    パーセントの取得
    """
    if not curent_value or not max_value:
        return u'0'
    from decimal import Decimal
    ret = (Decimal(curent_value ) / Decimal(max_value)) * Decimal('100')
    return int(ret)


@register.filter
def form_choiced_value(form_field):
    """
    フォームのChoiceFieldの、確認用の値を取得する
    ついでに、BooleanFieldの値も ON OFF で返す
    """
    if isinstance(form_field.field, forms.ChoiceField):
        value = form_field.data
        if value in forms.fields.EMPTY_VALUES:
            return u""
        for choice in form_field.field.choices:
            if value == str(choice[0]):
                return choice[1]
        return u''
    elif isinstance(form_field.field, forms.BooleanField):
        if form_field.data:
            return u'ON'
        else:
            return u'OFF'
    else:
        return form_field.data


@register.filter
def date_disp(datetime_object, fulldisp=False):
    """
    同じ日付だったら 時:分 違ってたら 月:日
    """
    if not datetime_object:
        return u''
    if fulldisp is False:
        days = datetime.datetime.now() - datetime_object
        if days.days == 0:
            return datetime_object.strftime("%H:%M")
        else:
            return datetime_object.strftime("%m/%d")
    else:
        return datetime_object.strftime("%m/%d %H:%M")


@register.filter
def truncate_width(source, width):
    """
    文字列をlength幅で切り詰めて表示
    widthは、全角=2,半角=1で計算する。
    """
    from module.common.text_spacer import string_width
    total_width = 0
    char_buffer = []
    for c in source:
        char_width = string_width(c)
        total_width += char_width
        if total_width > width:
            return u"".join(char_buffer)+u"…"
        char_buffer.append(c)
    return source


@register.filter
def ljustnbsp(value, width=6):
    """
    文字列が半角width分に足りなけれは、&nbsp;を追加
    """
    from module.common.text_spacer import ljustnbsp
    value = smart_unicode(value)
    return mark_safe(ljustnbsp(value, width))

@register.filter
def justifynbsp(value, width=6):
    """
    文字列が半角width分に足りなけれは、均等に&nbsp;を追加
    """
    from module.common.text_spacer import justifynbsp
    value = smart_unicode(value)
    return mark_safe(justifynbsp(value, width))

@register.filter
def concat_str(value, str):
    """
    文字連結
    """
    return u'%s%s' % (value, str)

_h2z_dict= {  u'ｱ' :u'ア', u'ｲ' :u'イ', u'ｳ' :u'ウ', u'ｴ' :u'エ', u'ｵ' :u'オ'
            , u'ｶ' :u'カ', u'ｷ' :u'キ', u'ｸ' :u'ク', u'ｹ' :u'ケ', u'ｺ' :u'コ'
            , u'ｻ' :u'サ', u'ｼ' :u'シ', u'ｽ' :u'ス', u'ｾ' :u'セ', u'ｿ' :u'ソ'
            , u'ﾀ' :u'タ', u'ﾁ' :u'チ', u'ﾂ' :u'ツ', u'ﾃ' :u'テ', u'ﾄ' :u'ト'
            , u'ﾅ' :u'ナ', u'ﾆ' :u'ニ', u'ﾇ' :u'ヌ', u'ﾈ' :u'ネ', u'ﾉ' :u'ノ'
            , u'ﾊ' :u'ハ', u'ﾋ' :u'ヒ', u'ﾌ' :u'フ', u'ﾍ' :u'ヘ', u'ﾎ' :u'ホ'
            , u'ﾏ' :u'マ', u'ﾐ' :u'ミ', u'ﾑ' :u'ム', u'ﾒ' :u'メ', u'ﾓ' :u'モ'
            , u'ﾔ' :u'ヤ', u'ﾕ' :u'ユ', u'ﾖ' :u'ヨ', u'ﾟ' :u'゜', u'ﾞ' :u'゛'
            , u'ﾗ' :u'ラ', u'ﾘ' :u'リ', u'ﾙ' :u'ル', u'ﾚ' :u'レ', u'ﾛ' :u'ロ'
            , u'ﾜ' :u'ワ', u'ﾝ' :u'ン', u'｢' :u'「', u'｣' :u'」', u'｡' :u'。'
            , u'､' :u'、', u'･' :u'・', u'ｧ' :u'ァ', u'ｨ' :u'ィ', u'ｩ' :u'ゥ'
            , u'ｪ' :u'ェ', u'ｫ' :u'ォ', u'ｬ' :u'ャ', u'ｭ' :u'ュ', u'ｮ' :u'ョ'

            , u'ｶﾞ':u'ガ', u'ｷﾞ':u'ギ', u'ｸﾞ':u'グ', u'ｹﾞ':u'ゲ', u'ｺﾞ':u'ゴ'
            , u'ｻﾞ':u'ザ', u'ｼﾞ':u'ジ', u'ｽﾞ':u'ズ', u'ｾﾞ':u'ゼ', u'ｿﾞ':u'ゾ'
            , u'ﾀﾞ':u'ダ', u'ﾁﾞ':u'ヂ', u'ﾂﾞ':u'ヅ', u'ﾃﾞ':u'デ', u'ﾄﾞ':u'ド'
            , u'ﾊﾞ':u'バ', u'ﾋﾞ':u'ビ', u'ﾌﾞ':u'ブ', u'ﾍﾞ':u'ベ', u'ﾎﾞ':u'ボ'
            , u'ﾊﾟ':u'パ', u'ﾋﾟ':u'ピ', u'ﾌﾟ':u'プ', u'ﾍﾟ':u'ペ', u'ﾎﾟ':u'ポ'
            , u'ｯ' :u'ッ'
            , u'ｳﾞ':u'ヴ'
            , u'ｦ' :u'ヲ', u'ｰ':u'ー'}

@register.filter
def z2h(str):
    dic = dict((v, k) for k, v in _h2z_dict.items())
    o = u'%s' % (unicode(str))
    r = []
    for i in o:
        r.append(i)
    r.reverse()
    o = u''
    for i in r:
        o = o + i
    z = u''
    p = u''
    for h in o:
        if h in dic:
            k = u'%s%s' % (h, p)
            if k in dic:
                z = dic[k]+z
            else:
                z= dic[h]+dic[p]+z
            p = u''
        else:
            if not p == u'':
                z = dic[p]+z
                p = u''
            z = h+z
    return z

@register.filter
def h2z(str):
    """
    半角カナを全角へ変換
    """
    dic = _h2z_dict
    daku = [u'ﾞ', u'ﾟ']
    o = u'%s' % (unicode(str))
    r = []
    for i in o:
        r.append(i)
    r.reverse()
    o = u''
    for i in r:
        o = o + i
    z = u''
    p = u''
    for h in o:
        if h in dic:
            if h in daku:
                if p in daku:
                    z = dic[p]+z # 前のものを全角の濁点、半濁点に変換
                p=u'%s' % (h)
            else:
                k = u'%s%s' % (h, p)
                if k in dic:
                    z = dic[k]+z
                else:
                    z= dic[h]+dic[p]+z
                p = u''
        else:
            if not p == u'':
                z = dic[p]+z
                p = u''
            z = h+z
    return z


@register.simple_tag(takes_context=True)
def cycle_global(context, arg1, arg2, arg3=None, arg4=None, arg5=None):
    """
    ループ状態をrequestに保存するcycle。
    """
    args = [arg1, arg2]
    def append_if_not_none(a):
        if a is not None:
            args.append(a)
    append_if_not_none(arg3)
    append_if_not_none(arg4)
    append_if_not_none(arg5)
    request = context.get('request', None)
    if not request:
        return arg1
    counter = getattr(request, 'cycle_global_counter', 0)
    result = args[counter % len(args)]
    request.cycle_global_counter = counter + 1
    return result

@register.simple_tag(takes_context=True)
def emoji2(context, name, enable_docomo_span=True):
    from module.common.emoji_char import emoji_char
    return emoji_char(name, context=context, enable_docomo_span=enable_docomo_span)


@register.simple_tag
def navi():
    html  = u"""<table class="table_full"><tr>"""
    html += u"""<td class="td_guide">%s</td>""" % guide_image_medium()
    html += u"""<td><div class="left">"""
    return html

@register.simple_tag
def endnavi():
    return u"""</div></td></tr></table>"""

@register.simple_tag(takes_context=True)
def accesskey_5_first(context):
    """
    テンプレート中で1回だけ、アクセスキー5を有効にする。
    ここでは絵文字は表示しない。
    """
    request = context.get('request')
    if not hasattr(request, 'is_printed_accesskey_5_first'):
        request.is_printed_accesskey_5_first = True
        return u' accesskey="5" '
    else:
        return u''

@register.simple_tag(takes_context=True)
def accesskey_5_first_emoji(context):
    """
    accesskey_5_first 用の絵文字を表示する
    """
    request = context.get('request')
    if not hasattr(request, 'is_printed_accesskey_5_first'):
        return emoji2(context, 'five')
    else:
        return u''

@register.filter
def remove_invalid_unicode(text):
    from module.utils import remove_invalid_unicode
    return remove_invalid_unicode(text)


@register.simple_tag
def countdown(datetime_or_string, format_text=u'あと%s', expired_text=u'まもなく終了'):
    """
    引数にdatetimeか %Y-%m-%d %H:%M:%S 形式の文字列をとり、
    「ｱﾄ◯日と◯時間」 みたいに表示する
    expired_text は、1分以下で表示。時間を超えても出る
    """
    from module.utils import countdown
    return countdown(datetime_or_string, format_text=format_text, expired_text=expired_text)


#==================================================
# ifbefore, ifafter, ifafterbefore
#--------------------------------------------------
from django.template import NodeList #Node,

class IfAfterBeforeNode(Node):
    child_nodelists = ('nodelist_true', 'nodelist_false')
    datestr_format_list = ('%Y-%m-%d %H:%M:%S', '%Y-%m-%d', '%H:%M:%S')

    def __init__(self, var_after, var_before, nodelist_true, nodelist_false=None):
        self.nodelist_true, self.nodelist_false = nodelist_true, nodelist_false
        self.var_after = var_after
        self.var_before = var_before
        self.now = datetime.datetime.now()

    def strptime(self, date_string):
        """
        日付文字列をパースしてdatetimeにする。
        パースできなければNone
        """
        date_string = date_string.strip("""'" """)
        for datestr_format in self.datestr_format_list:
            try:
                return datetime.datetime.strptime(date_string, datestr_format)
            except ValueError:
                pass
        return None

    def __repr__(self):
        return "<IfBeforeAfter node>"

    def __iter__(self):
        for node in self.nodelist_true:
            yield node
        for node in self.nodelist_false:
            yield node

    def arg_to_dt_or_none(self, arg, context):
        """
        引数を datetime もしくは none として取得
        self.var_after, self.var_before に使う
        """
        if not arg:
            return None
        try:
            # 引数がdatetimeの場合があるので
            dt = resolve_variable(arg, context)
        except template.VariableDoesNotExist:
            dt  = None
        if dt is None or not isinstance(dt,  datetime.datetime):
            dt = self.strptime(arg)
        return dt

    def render(self, context):

        dt_after  = self.arg_to_dt_or_none(self.var_after,  context)
        dt_before = self.arg_to_dt_or_none(self.var_before, context)

        if dt_after and dt_before:
            if dt_after <= self.now < dt_before:
                return self.nodelist_true.render(context)
            else:
                return self.nodelist_false.render(context)
        elif dt_after:
            if dt_after <= self.now:
                return self.nodelist_true.render(context)
            else:
                return self.nodelist_false.render(context)
        elif dt_before:
            if self.now < dt_before:
                return self.nodelist_true.render(context)
            else:
                return self.nodelist_false.render(context)
        else:
            return u'Parse Error. No after, before'

@register.tag
def ifbefore(parser, token):
    """
    現在日時が"YYYY-MM-DD HH:MM:SS" より前(未満)であればレンダリング
    """
    _tagname, var_before = token.split_contents()
    nodelist_true = parser.parse(('else', 'endifbefore'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifbefore',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return IfAfterBeforeNode(None, var_before, nodelist_true, nodelist_false)

@register.tag
def ifafter(parser, token):
    """
    現在日時が"YYYY-MM-DD HH:MM:SS" より後(以上)であればレンダリング
    """
    _tagname, var_after = token.split_contents()
    nodelist_true = parser.parse(('else', 'endifafter'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifafter',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return IfAfterBeforeNode(var_after, None, nodelist_true, nodelist_false)

@register.tag
def ifafterbefore(parser, token):
    """
    2つの引数をとり、現在時刻がその以上未満であればレンダリング
    """
    _tagname, var_after, var_before = token.split_contents()

    nodelist_true = parser.parse(('else', 'endifafterbefore'))
    token = parser.next_token()
    if token.contents == 'else':
        nodelist_false = parser.parse(('endifafterbefore',))
        parser.delete_first_token()
    else:
        nodelist_false = NodeList()
    return IfAfterBeforeNode(var_after, var_before, nodelist_true, nodelist_false)


@register.filter
def weekday_ja(dt):
    """日本語の曜日"""
    weekday_list = [u'月',u'火',u'水',u'木',u'金',u'土',u'日',]
    return weekday_list[dt.weekday()]


@register.simple_tag
def useticket_item_name(item_id):
    ticket_item = item_api.get_item(item_id)
    html = '%s' % ticket_item.name
    return html

@register.simple_tag
def useticket_item_name_sp(item_id):
    ticket_item = item_api.get_item(item_id)
    html = '%s' % h2z(ticket_item.name)
    return html

@register.simple_tag
def useticket_item_count(player, item_id):
    ticket_gashapon_item = get_player_item_from_item(player, item_id)
    html = '%s' % ticket_gashapon_item.number
    return html

@register.simple_tag
def useticket_view_flag(player, item_id):
    ticket_gashapon_item = get_player_item_from_item(player, item_id)

    if ticket_gashapon_item.number > 0 :
        return True
    else :
        return False

@register.simple_tag
def sub_header_img():
    """
    水平線画像
    """
    html = u'<img src="%s/imgs/common/line/line01_240x2.gif" style="width:240px;height:2px;"/>' % media_url()
    return html

@register.filter
def now_timestamp(dummy):
    '現在日時のタイムスタンプを返すフィルタ'
    return DatetimeUtil.datetime_to_timestamp(DatetimeUtil.now())

@register.filter
def str_to_timestamp(datetime_str):
    '文字列日時をタイムスタンプに変換する'
    return DatetimeUtil.str_to_timestamp(datetime_str)

@register.filter
def is_earlier_than_now(datetime_str):
    '指定文字列時刻が現在時刻より前か'
    now = DatetimeUtil.datetime_to_timestamp(DatetimeUtil.now())
    ts = DatetimeUtil.str_to_timestamp(datetime_str)
    return ts < now

@register.filter
def is_later_than_now(datetime_str):
    '指定文字列時刻が現在時刻より後か'
    now = DatetimeUtil.datetime_to_timestamp(DatetimeUtil.now())
    ts = DatetimeUtil.str_to_timestamp(datetime_str)
    return ts > now

@register.filter
def datetime_to_timestamp(datetime_obj):
    '日時をタイムスタンプに変換する'
    return DatetimeUtil.datetime_to_timestamp(datetime_obj)

@register.filter
def is_spurt(days, end_at):
    '''
    イベントスパート期間か
    '''
    if not end_at:
        return False
    if (end_at - DatetimeUtil.now()).days > int(days):
        return False
    return True

@register.simple_tag
def rest_event_date(days, end_at, default_msg=u""):
    '''
    イベント残り日数（時間）表示
    '''
    if not end_at:
        return mark_safe(default_msg)
    if (end_at - DatetimeUtil.now()).days > int(days):
        return mark_safe(default_msg)
    rest_str = rest_datetime_by_timedelta(end_at - DatetimeUtil.now())
    return mark_safe(u'<span style="color:#F00">終了まで残り%s!!</span>' % rest_str)

@register.simple_tag
def rest_datetime(end_at, default_msg=u"", color='color_red', blink="blink"):
    '''
    イベント残り日数（時間）表示
    '''
    if not end_at:
        return mark_safe(default_msg)
    rest_str = rest_datetime_by_timedelta(end_at - DatetimeUtil.now())
    return mark_safe(u'<span class="%s %s">ｱﾄ%s!!</span>' % (color, blink, rest_str))

def rest_datetime_by_timedelta(timedelta, is_minitue=False):
    '''
    time deltaから残りの日数、時間を出す
    '''
    days = timedelta.days

    if days > 0:
        hours = (timedelta.seconds / 60 / 60)
    else:
        hours = timedelta.days * 24 + (timedelta.seconds / 60 / 60)
    minitue = (timedelta.seconds / 60 % 60)
    second = timedelta.seconds

    output = ''
    if days >= 1:
        output += u'%s日' % (days)
        if hours > 0:
            output += u'と%s時間' % (hours)
        if is_minitue:
            output += u'%s分' % (minitue)
    elif hours >= 1:
        output += u'%s時間' % (hours)
        if minitue > 0:
            output += u'と%s分' % (minitue)
    elif minitue >= 1:
        output += u'%s分' % (minitue)
    elif second >= 1:
        output += u'%s秒' % (second)
    else:
        output = ''
    return output


@register.simple_tag
def rest_time_s(end_at, show_id="default_id",css_class="color_red"):
    '''
    イベント残り日数（時間）表示
    '''

    remaining_time = time.mktime(end_at.utctimetuple())

    show_tag = u"""
        <span id="%s" class="%s"></span>
        <script language="JavaScript"><!--
        // 時間を整形する

        function TimeFormat(time_d,time_h,time_m,time_s){
          var str = "";
          var tmp;

          if(time_d){
          str += String( time_d );
          str += "日";
          }

          if(time_h < 24){
            tmp = "00" + String( time_h );
            str += tmp.substr(tmp.length - 2);
          }else{
            str += String( time_h );
          }
          str += "時間";
          tmp = "00" + String( time_m );
          str += tmp.substr(tmp.length - 2);
          str += "分";
          tmp = "00" + String( time_s );
          str += tmp.substr(tmp.length - 2);
          str += "秒";

          return str;
        }


        // 残り時間を表示する
        function TimeRemaining(end_unixtime){
          var now_unixtime = parseInt((new Date)/1000);

          var tmp = end_unixtime - now_unixtime;

          if(tmp < 0){
            tmp = 0;
          }

          var time_d = Math.floor(tmp/86400);
          if(time_d){
              tmp -= (time_d*86400);
          }

          var time_h = Math.floor(tmp/3600);
          if(time_h){
              tmp -= time_h*3600;
          }


          var time_m = Math.floor(tmp/60);
          if(time_m){
              tmp -= time_m*60;
          }


          var time_s = tmp;

          return TimeFormat(time_d,time_h,time_m,time_s);
        }

        // 残り時間をdiv領域に表示する動作を一定間隔で繰り返す
        function TimeRemainingView(){
          document.getElementById("%s").innerHTML=TimeRemaining(%s);
          setTimeout("TimeRemainingView()",100);
        }

        TimeRemainingView();

        // -->
        </script>

    """



    return mark_safe(show_tag % (show_id,css_class,show_id,remaining_time))



@register.simple_tag
def rest_datetime_cp(end_at, default_msg=u"", color='color_light_pink', font='font12'):
    '''
    ヒール残り日数（時間）表示
    '''
    if not end_at:
        return mark_safe(default_msg)
    if end_at <= DatetimeUtil.now():
        return ''

    rest_str = rest_datetime_by_timedelta_cp(end_at.replace(microsecond=0) - DatetimeUtil.now().replace(microsecond=0))
    return mark_safe(u'<span class="%s %s">ｱﾄ%s</span>' % (color, font, rest_str))


def rest_datetime_by_timedelta_cp(timedelta, is_minitue=False):
    '''
    time deltaから残りの日数、時間を出す
    '''

    hours = timedelta.days * 24 + (timedelta.seconds / 60 / 60)
    minute = (timedelta.seconds / 60 % 60)
    second = timedelta.seconds - minute * 60 - hours * 60 * 60

    return "{0:02d}:{1:02d}:{2:02d}".format(hours, minute, second)

@register.filter
def num_to_range(num):
    return range(1,num+1)


@register.filter
def num_to_range_min(num, min=1):
    print(min)
    if not min:
        min = 1
    return range(min,num+1)


@register.tag(name="smartform")
def do_smartform(parser, token):
    nodelist = parser.parse(('endsmartform',))
    parser.delete_first_token()
    return SmartFormNode(nodelist)

class SmartFormNode(template.Node):
    '''
    HTMLフォームで扱う定型処理の自動化

    # viwe.py
    def render(request, name, param):
        ctxt = RequestContext(request, {'foo': 2})
        return render_to_response('foobar.html', ctxt)

    # html
    {% smartform %}
    <form>
        <select name="foo">
            <option value="">default</option>
            <option value="1">one</option>
            <option value="2">two</option>
        </select>
    </form>
    {% endsmartform %}
    '''
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        self.param  = context.get('smartform', {})
        output      = self.nodelist.render(context)
        re_select   = re.compile(r'''<select\s[^>]*name=(['"])(.+?)\1.+?>(.+?)</select>''', re.DOTALL)
        output      = re_select.sub(self.convert_select, output)
        return output

    def convert_select(self, match):
        ''' 多くの場合にこれで十分と思うが、ケースバイケースで対応してください '''
        output  = match.group(0)
        name    = match.group(2)
        if not name in self.param:
            return output
        value  = self.param.get(name)
        output = re.sub(r'''option value\s*=\s*(['"])%s\1''' % value,
                'option value="%s" selected="selected"' % value,
                output)
        return output

    def convert_radio(self, match):
        ''' TODO 必要に迫られたら実装してください '''
        return output


#
# 以下はデバッグ用カードを出力するタグ。不要になったら消す
# {% with debug_card as card %}
@register.filter
def debug_card(card_id):
    from module.card.api import get_card
    if not card_id.isdigit():
        card_id = 10001011
    card = get_card(card_id)
    return card


@register.filter
def debug_player_card(player):
    from playercard.api import acquire_card
    return acquire_card(player, 10001011)


@register.filter
def debug_swf(swf_name):
    swf_name = "{}/{}".format(media_url(), swf_name)
    swf_tag = """
<object type="application/x-shockwave-flash" data="{}" width="240" height="240" id="flash-sample">
<param name="movie" value="{}">
</object>
""".format(swf_name, swf_name)
    return mark_safe(swf_tag)

@register.filter
def debug_boss(boss_id):
    from module.stage.api import get_quest_boss_by_quest_id
    return get_quest_boss_by_quest_id(boss_id)

@register.inclusion_tag('partial/comment.html', takes_context=True)
def balloom_comment(context,comment,element,idx):
    cxt = RequestContext( context['request'],{
        'comment':comment,
        'element': element,
        'idx': idx,
        })
    return cxt


@register.tag
class player_card_showcase(template.Node):
    def __init__(self, parser, token):
        tokens = token.split_contents()
        self.cards = tokens[1]
        self.editable = False
        if len(tokens) > 2:
            self.editable = bool(tokens[2])

    def __call__(self):
        return self

    def render(self, context):
        from module.stage.boss import boss_battle_member_choice, boss_battle_member_select
        request = context['request']
        card_order = (5, 3, 1, 2, 4)
        cards = resolve_variable(self.cards, context)
        quest_id = resolve_variable('player_quest_id', context)

        url_convert = opensocial_url_convert

        player_card_list = []
        for position in card_order:
            position -= 1
            card = cards[position]
            if card is None:
                card = get_dummy_card()
            if position in (3, 4):
                card.link = url_convert(reverse('boss_battle_friend_list', args=[quest_id, position - 3, 1]))
            else:
                link = boss_battle_member_choice.callback(boss_battle_member_select, args=(position, ), params={'quest_id':quest_id, 'position':position})
                card.link = url_convert(link)
            card.level = unicode(getattr(card, 'level', ''))
            player_card_list.append(card)

        context['player_card_list'] = player_card_list
        context['editable'] = self.editable
        return render_to_string('partial/card_show_case.html', context)


@register.simple_tag(takes_context=True)
def player_thumbnail(context, player, size="normal"):
    """ GREE スマホ版は data-gree-src というタグだよ"""
    if not player:
        return ''
    if settings.IS_GREE:
        SIZE_MAP = {
            "small": (player.thumbnail_url_s, 25),
            "normal": (player.thumbnail_url, 48),
            "card_short": (player.thumbnail_url, 60),
            "large": (player.thumbnail_url_l, 76)
            }
    else:
         SIZE_MAP = {
            "small": (player.thumbnail_url_s, 25),
            "normal": (player.thumbnail_url, 48),
            "card_short": (player.thumbnail_url, 71),
            "large": (player.thumbnail_url_l, 76)
            }
    thumbnail_url, size = SIZE_MAP.get(size, (player.thumbnail_url, 48))
    thumbnail_img = u""
    request = context.get('request')

    if (settings.IS_MBGA or settings.IS_DGAME) and hasattr(player, 'pk'):
        from gsocial.set_container import Container
        container = Container(request)
        view_size = 'medium'
        if size == 'large':
            view_size = 'large'
        if settings.IS_MBGA:
            params = 'size={};dimension=defined;emotion=normal;transparent=true;view=upper'.format(view_size)
        else:
            params = 'size={};type=image;view=upper'.format(view_size)

        data = container.get_avatar_self(player.pk, params=params)
        if data:
            thumbnail_url = data.get('url', '')

    if settings.IS_MIXI and request and request.is_smartphone:
        thumbnail_url = thumbnail_url.replace("http://", "https://")

    if settings.IS_GREE and request and request.is_smartphone:
        thumbnail_img = '<img data-gree-src="{}" width="{}" alt="ﾏｽﾀｰ" />'.format(thumbnail_url, size)
    elif settings.IS_MBGA and request and request.is_smartphone:
        thumbnail_img = '<img src="{}" width="{}" alt="ﾏｽﾀｰ" />'.format(thumbnail_url, size)
    else:
        if size == 48:
            # FPのnormalは40で。
            if settings.IS_GREE:
                size = 40
            elif settings.IS_DGAME:
                size = 50
            else:
                size = 30

        if settings.IS_AMEBA:
            size = 50

        thumbnail_img = '<img src="{}" width="{}" alt="ﾏｽﾀｰ" />'.format(thumbnail_url, size)
    return mark_safe(thumbnail_img)


@register.tag
class callback(template.Node):
    def __init__(self, parser, token):
        tokens = token.split_contents()
        self.args = tokens[1:]

    def __call__(self):
        return self

    def render(self, context):
        request = context['request']
        args = [unicode(resolve_variable(arg, context)) for arg in self.args]
        convert = opensocial_url_convert
        return convert(reverse('callback_receiver', args=[u'/'.join(args)]))

@register.inclusion_tag('partial/sort_selector.html', takes_context=True)
def sort_selector(context, sort_key_list, sort_key_idx, element=None):
    request = context['request']
    return {
        'next_url': opensocial_url_convert(request.path),
        'sort_key_list': sort_key_list,
        'sort_key_idx': sort_key_idx,
        'element': element,
    }

@register.simple_tag(takes_context=True)
def navi_image(context, face='normal', width=70, height=70):
    '''
    ナビキャラ画像表示
    '''
    request = context.get('request')

    if not width or not height:
        if request.is_smartphone:
            width = 140
            height = 140
    navi = Navi()
    html = u'<img src="%s" width="%d" height="%d" />' % (navi.image_url[face], width, height)
    return html

# @register.inclusion_tag('partial/element_selector.html', takes_context=True)

@register.tag
class element_selector(template.Node):
    def __init__(self, parser, token):
        tokens = token.split_contents()
        self.element_list = tokens[1]
        self.current_element_index = tokens[2]
        self.use_all = tokens[3] if len(tokens) > 3 else None

    def __call__(self):
        return self

    def render(self, context):
        request = context['request']
        element_list = resolve_variable(self.element_list, context)
        current_element_index = int(resolve_variable(self.current_element_index, context))
        use_all = resolve_variable(self.use_all, context)

        url_convert = opensocial_url_convert

        link = []
        if use_all:
            link.append({'id':0, 'name':u'全部', 'link':url_convert(request.path, {'element': '0'})})

        for i, el in enumerate(element_list):
            link.append({'id':el.id, 'name': el.name, 'link':url_convert(request.path, {'element': str(el.id)})})

        context['element_link_list'] = link

        return render_to_string('partial/element_selector.html', context)

@register.simple_tag
def card_love_image(card):

    # love/max_love が計算できないものは画像表示しない
    if not hasattr(card,'love'):
        return ''
    if not hasattr(card,'max_love'):
        return ''

    elif card.max_love==0:
        # 招待カードなどには忠誠度の概念がないため、忠誠度のアイコン上は常に「空」
        love_rank = 1
    else:
        love_percentage = 100 * card.love / card.max_love
        if love_percentage <= 25:
            love_rank = 1
        elif love_percentage < 50:
            love_rank = 2
        elif love_percentage < 75:
            love_rank = 3
        elif love_percentage < 100:
            love_rank = 4
        else:
            love_rank = 5

    # 画像の表示サイズをスマホ/ガラケで変える
    from common.deviceenvironment.device_environment import is_smartphone
    if is_smartphone():
        img_size = 17
    else:
        img_size = 14
    img = u'<img src="%s/imgs/card/shinai/love_%s.gif" style="width:%spx;height:%spx;" />' % (media_url(), love_rank, img_size, img_size)
    return img

@register.simple_tag
def cooperate_banner_rand(view_mode="default"):
    '''
    外部連携バナーをアクティブに出す
    '''
    from common.deviceenvironment.device_environment import is_smartphone
    html = u''

    l = None
    if view_mode == "default":
        l = getattr(settings, 'COOPERATE_BANNERS_ALWAYS', [])
    elif view_mode == "maintenance":
        l = getattr(settings, 'COOPERATE_MAINTENANCE_BANNERS_ALWAYS', [])
    if not l:
        return html

    base_url = getattr(settings, 'COOPERATE_BANNERS_LINK_URL', None)
    if not base_url:
        return html

    env = 'fp'
    if is_smartphone():
        env = 'sp'

    base_url = base_url[env]
    idx = random.randint(0, len(l)-1)
    info = l[idx]
#    img = u'<img src="%s/%s" style="width:%spx;height:%spx;" />' % (media_url(), info['url'], img_size, img_size)
    if env == 'sp':
        html = u'<a href="%s" target="_top"><img src="%s/%s" width="200" /><br />%s</a>' % (base_url.format(info['id']), media_url(), info['img'], info['title'])
    else:
        html = u'<a href="%s"><img src="%s/%s" /><br />%s</a>' % (base_url.format(info['id']), media_url(), info['img'], info['title'])
    return html

@register.inclusion_tag('partial/main_buttons.html', takes_context=True)
def call_main_buttons_html(context):
    request = context['request']
    if 'event' not in context or not hasattr(request, "event"):
        from module.bannerarrange.api import get_event_banner
        from eventmodule.ecommon.api import get_enable_events

        event = get_enable_events()
        if event:
            event_banner = get_event_banner(event[-1])
            context["event_controller"] = event_banner
            context["event"] = event[0]
    if 'campaign' not in context or not hasattr(request, "campaign"):
        context["campaign"] = get_active_buildup_campaign(request.player)

    return context


@register.filter
def list_acccess(l, idx):
    return l[idx]


@register.tag
def new_pager(parser, token):
    """
    ページ移動式のページャー。urlsの可変長引数に対応している版
    {% new_pager pager 'root_index' 1 %}
    @authoer Nodeの使い方が分からんorz @sada
    """
    file_name = "partial/new_pager.html"
    bits = token.split_contents()
    if len(bits) < 3:
        raise template.TemplateSyntaxError("%r tag requires <pager> <url> " % token.contents.split()[0])

    class PagerNode(TagHelperNode):
        def render(self, context):
            args = [resolve_variable(arg, context) for arg in bits[1:]] # タグ名以外を変数展開
            _pager, url_name, args = args[0], args[1], args[2:]
            _pager.omission_pages = _pager.get_omission_pages()
            for page in _pager.omission_pages:
                if page.omission or page == _pager.current:
                    pass
                else:
                    paged_args = args + [page.number]
                    page.paged_url = url_to_opensocial_url_switcher(reverse(url_name, args=paged_args), context)
            context['pager'] = _pager
            t = get_template(file_name)
            return t.render(context)
    return PagerNode(takes_context=True, args=(), kwargs={})


@register.tag
def include_anim(parser, token):
    try:
        bits = token.split_contents()
        path = resolve_variable(bits[1], context)
    except template.VariableDoesNotExist:
        path = bits[1]
        if path[0] in ('"', "'") and path[-1] == path[0]:
            path = path[1:-1]
    from django.template.loader_tags import IncludeNode
    from common.deviceenvironment.device_environment import media_root
    path = media_root() + '/anims/' + path
    # return ConstantIncludeNode(path[1:-1], extra_context={}, isolated_context=False)
    return IncludeNode(parser.compile_filter(path), extra_context={}, isolated_context=False)


@register.tag
class define(template.Node):
    """
    {% define %}
aaa=今日の+T.CARD+は
緑色の+player.cards.0.name+です,
ccc=ccc,
{% enddefine %}

{% include './partial/section_title.html' with title=aaa class="section_title" %}
{{ ccc }}
    """
    def __init__(self, parser, token):
        self.nodelist = parser.parse(('enddefine',))
        parser.delete_first_token()

    def __call__(self):
        return self

    def render(self, context):
        defined_context = {}
        self.defines_str = self.nodelist.render(context)
        defines_strs = self.defines_str.split(",")
        for _define in defines_strs:
            key, _, val = _define.strip().partition("=")
            vals = val.split("+")

            resolve_vals = []
            for val in vals:
                if not val:
                    continue
                try:
                    val = resolve_variable(val, context)
                except (VariableDoesNotExist, UnicodeEncodeError):
                    pass
                resolve_vals.append(val)
            try:
                resolve_vals = [str(x) for x in resolve_vals]
            except UnicodeEncodeError:
                pass
            resolve_val = "".join(resolve_vals)
            defined_context[key] = linebreaksbr(mark_safe(resolve_val))
        context.update(defined_context)
        return ""

def get_defined_context(defines_str, context):
    """ ↑ の define の分解部分のみ抽出.上は動いているので手を出さない  """
    defined_context = {}
    defines_strs = defines_str.split(",")
    for _define in defines_strs:
        key, _, val = _define.strip().partition("=")
        vals = val.split("+")

        resolve_vals = []
        for val in vals:
            if not val:
                continue
            try:
                val = resolve_variable(val, context)
            except (VariableDoesNotExist, UnicodeEncodeError):
                pass
            resolve_vals.append(val)
        resolve_val = "".join(resolve_vals)
        defined_context[key] = linebreaksbr(mark_safe(resolve_val))
    return defined_context


@register.simple_tag(takes_context=True)
def define_include(context, template_name):
    """
    {% defineinclude "root/index.html" %}

    # root/index.html
    aaa=今日の+T.CARD+は
    緑色の+player.cards.0.name+です,
    ccc=ccc,
    """
    try:
        template = get_template(template_name)
    except:
        if settings.TEMPLATE_DEBUG:
            raise
        return ''

    defines_str = template.render(context)
    defined_context = get_defined_context(defines_str, context)
    context.update(defined_context)
    return ""

@register.tag
class str_format(template.Node):
    """
    {% str_format {}の{}は{}です T.CARD_DECK T.ATTACK_POWER player.attack %}
    """
    def __init__(self, parser, token):
        bits = token.contents.split()
        if len(bits) < 3:
            raise template.TemplateSyntaxError("%r tag requires <fromat_str> <...> " % token.contents.split()[0])

        self.format_string = bits[1]
        self.args = bits[2:]

    def __call__(self):
        return self

    def render(self, context):
        try:
            args = [resolve_variable(arg, context) for arg in self.args]
        except VariableDoesNotExist:
            pass
        return self.format_string.format(*args)


@register.simple_tag
def replace(base, old, new):
    return base.replace(old, new)


@register.filter
def stars(number):
    star = u''
    try:
        number = int(number)
        if number == 0:
            star = u'　'
        for i in range(0, number):
            star += u'★'
    except ValueError:
        pass
    return star


@register.tag
class img(template.Node):

    def __init__(self, parser, token):
        bits = token.contents.split()
        self.img_path = bits[1]
        self.style = ';'.join(bits[2:])

    def __call__(self):
        return self

    def render(self, context):
        device = 'sp' if context['request'].is_smartphone else 'fp'

        attrs = {}
        try:
            attrs['src'] = resolve_variable(self.img_path, context)
        except VariableDoesNotExist:
            attrs['src'] = ''

        image_size_settings = settings.ITEM_IMAGE_SIZE
        if "card" in attrs['src']:
            image_size_settings = settings.IMAGE_SIZE
        elif "treasureseries" in attrs['src']:
            image_size_settings = settings.TREASURE_IMAGE_SIZE
        elif "thumbnail:show" in attrs['src']:
            image_size_settings = settings.PLAYER_IMAGE_SIZE

        _, size_name = self.img_path.rsplit('.', 1)
        attrs.update(image_size_settings[device].get(size_name.lower(), {}))

        if self.style:
            style = dict((k.strip(), v.strip()) for k, v in [x.split(':') for x in self.style.split(';') if x])
            if "class" in style:
                attrs["class"] = style.pop("class")
            attrs['style'] = ';'.join('{}:{}'.format(k, v) for k, v in style.items())
            if 'width' in style:
                attrs['width'] = style['width']
            if 'height' in style:
                attrs['height'] = style['height']

        # html5は html属性よりcssが優先されることになった
        if device == 'sp':
            attrs["style"] = u"width:{}px;height:{}px;".format(attrs.get("width"), attrs.get("height")) + attrs.get("style", "")

        if device == "sp" and "thumbnail:show" in attrs['src']:
            attrs['data-gree-src'] = attrs.pop('src')

        # シェイク対応
        # try:
        #     if device == "sp" and "card" in attrs['src'] and size_name == "large":
        #         card = resolve_variable(self.img_path.split('.', 1)[0], context)
        #         if card.flag_is_shake():
        #             context.update({
        #                 "card_id": card.id,
        #                 "img_uri": attrs['src']
        #             })
        #             return render_to_string("card/partial/shake.html", context)
        # except:  # 何が起きてもエラーにしない
        #     pass

        return u'<img ' + u' '.join(u'{}="{}"'.format(k, v) for k, v in attrs.items()) + u' />'


@register.inclusion_tag('common/menu_banner.html', takes_context=True)
def menu_banner_tag(context):
    from module.bannerarrange.api import get_banner_tag, get_active_sp_mini_arrange_list
    from module.bannerarrange.models import ArrangeBase

    banner_list = get_active_sp_mini_arrange_list()
    banners_menu = get_banner_tag(ArrangeBase.GLOBALMENU_TOP, banner_list)
    context['banners_menu'] = banners_menu[:2]

    return context


@register.tag
class voice(template.Node):
    def __init__(self, parser, token):
        bits = token.contents.split()
        self.path = bits[1]
        self.template_path = 'card/partial/voice.html'
        try:
            self.template_path = bits[2]
        except IndexError:
            pass

    def __call__(self):
        return self

    def render(self, context):
        device = 'sp' if context['request'].is_smartphone else 'fp'
        if device == "fp":
            try:
                voice_comment = resolve_variable(self.path, context)
            except VariableDoesNotExist:
                return ''
        else:
            # SP
            try:
                obj_path, comment_field = self.path.rsplit('.', 1)
                obj = resolve_variable(obj_path, context)
            except VariableDoesNotExist:
                return ''

            if isinstance(obj, PlayerCard):
                card = obj.card
                comment = getattr(obj.card.detail, comment_field)
            elif isinstance(obj, Card):
                card = obj
                comment = getattr(obj.detail, comment_field)
            elif isinstance(obj, CardDetail):
                card = get_card(obj.id)
                comment = getattr(obj, comment_field)
            else:
                return ""

            return self.render_if_voice(context, card, comment, comment_field)

    def render_if_voice(self, context, card, comment, comment_field):
        if card.flag_is_voice():
            return self.render_for_voice(context, card, comment, comment_field)
        else:
            return comment

    def render_for_voice(self, context, card, comment, comment_field):
        ''' 音声再生ボタン付き出力 '''
        voice_url = card.detail.voice_url.get(comment_field)
        if not voice_url:
            return comment
        context.update({
            "comment": comment,
            "voice_urls": ",".join([voice_url])
            })
        return render_to_string("card/partial/voice.html", context)


@register.tag
class voice_all(voice):
    ''' 全音声出力(ループ)用 '''
    def render_for_voice(self, context, card, comment, comment_field):
        ''' 音声再生ボタン付き出力 '''
        voice_url = card.detail.voice_url.get(comment_field)
        if not voice_url:
            return comment
        voice_urls = [card.detail.voice_url["{:02d}".format(i)] for i in range(1, 14 + 1)]
        context.update({
            "comment": comment,
            "voice_urls": ",".join(voice_urls)
            })
        return render_to_string("card/partial/voice.html", context)


@register.tag
class voice_single(voice):
    ''' 音声出力(単発)用 '''
    def render_if_voice(self, context, card, comment, comment_field):
        return self.render_for_voice(context, card, comment, comment_field)

    def render_for_voice(self, context, card, comment_function, comment_dummy2):
        ''' 吹き出し付き出力 '''
        comment_field = comment_function()
        comment = getattr(card.detail, comment_field)
        voice_url = card.detail.voice_url.get(comment_field)
        context.update({
            "comment": comment,
            "element": card.element,
            "voice_urls": "",
        })
        if card.flag_is_voice() and voice_url:
            context["voice_urls"] = voice_url

        return render_to_string(self.template_path, context)


@register.tag
class voice_miyabi(voice):
    ''' 音声出力(ループ)用 '''
    def render_for_voice(self, context, card, comment, comment_field):
        ''' 音声再生ボタン付き出力 '''
        voice_url = card.detail.voice_url.get(comment_field)
        if not voice_url:
            return comment
        voice_urls = [card.detail.voice_url["{:02d}".format(i)] for i in range(1, 3)]
        context.update({
            "comment": comment,
            "voice_urls": ",".join(voice_urls)
            })
        return render_to_string("card/partial/voice_miyabi.html", context)

@register.tag
class voice_miyabi_mybed(voice):
    ''' 音声出力(ループ)用 '''
    def render_for_voice(self, context, card, comment, comment_field):
        ''' 音声再生ボタン付き出力 '''
        voice_url = card.detail.voice_url.get(comment_field)
        if not voice_url:
            return comment
        voice_urls = [card.detail.voice_url["{:02d}".format(i)] for i in range(2, 3)]
        context.update({
            "comment": comment,
            "voice_urls": ",".join(voice_urls)
            })
        return render_to_string("card/partial/voice_miyabi_mybed.html", context)

@register.filter(name='avoid_commodity_image_fp')
def avoid_commodity_image_fp(commodity):
    from gachamodule.fgacha.constants import C
    return C(commodity.gashapon).AVOID_COMMODITY_IMAGE_FP


@register.filter(name='avoid_commodity_image_sp')
def avoid_commodity_image_sp(commodity):
    from gachamodule.fgacha.constants import C
    return C(commodity.gashapon).AVOID_COMMODITY_IMAGE_SP


@register.filter(name='is_long_banner')
def is_long_banner(commodity):
    from gachamodule.fgacha.constants import C
    return C(commodity.gashapon).is_long_banner(commodity.quantity)


@register.filter(name='special_gacha_bannear_arrange_sp')
def special_gacha_bannear_arrange_sp(value):
    from gachamodule.fgacha.models import Gashapon
    special_gashapons = [x for x in Gashapon.get_cache_all() if x.is_enable and
#                         x.module in ('limitedgacha', 'luckygacha')]
                         x.module in ('luckygacha')]
    if special_gashapons:
        special_gashapon = special_gashapons[0]
        from gachamodule.fgacha.constants import C
        banner_id = getattr(C(special_gashapon), 'BANNER_ARRANGE_ID_SP', None)
        if banner_id:
            from module.bannerarrange.models import ArrangeSp
            banner = ArrangeSp.get_cache(banner_id)
            if banner and banner.get_banner().is_enable:
                from module.bannerarrange.api import create_banner_tag
                return create_banner_tag(banner)

    return u''


@register.filter(name='special_gacha_bannear_arrange_fp')
def special_gacha_bannear_arrange_fp(value):
    from gachamodule.fgacha.models import Gashapon
    special_gashapons = [x for x in Gashapon.get_cache_all() if x.is_enable and
#                         x.module in ('limitedgacha', 'luckygacha')]
                         x.module in ('luckygacha')]
    if special_gashapons:
        special_gashapon = special_gashapons[0]
        from gachamodule.fgacha.constants import C
        banner_id = getattr(C(special_gashapon), 'BANNER_ARRANGE_ID_FP', None)
        if banner_id:
            from module.bannerarrange.models import ArrangeFp
            banner = ArrangeFp.get_cache(banner_id)
            if banner and banner.get_banner().is_enable:
                from module.bannerarrange.api import create_banner_tag
                return create_banner_tag(banner)

    return u''


@register.tag('pjaxviaproxy')
def do_pjaxviaproxy(parser, token):
    nodelist = parser.parse(('endpjaxviaproxy', ))
    parser.delete_first_token()
    return HtmlBodyNode(nodelist)


class HtmlBodyNode(template.Node):
    def __init__(self, nodelist):
        self.nodelist = nodelist

    def render(self, context):
        output = self.nodelist.render(context)
        if context.get('pjax_via_container', False):
            return u'<html><body>' + output + u'</body></html>'
        else:
            return output

@register.simple_tag
def rest_datetime_param(end_at, default_msg=u"", color='color_red', blink="blink"):
    '''
    パラメータの残り日数（時間）表示
    '''
    if not end_at:
        return mark_safe(default_msg)
    rest_str = rest_datetime_by_timedelta(end_at - DatetimeUtil.now())
    return mark_safe(u'<span class="%s %s">ｱﾄ%s!!</span>' % (color, blink, rest_str))

@register.simple_tag
def reset_detetime_by_mmss(end_at):
    '''
    パラメータの残り時間の分秒を表示
    '''
    timedelta = end_at.replace(microsecond=0) - DatetimeUtil.now().replace(microsecond=0)

    hours = timedelta.days * 24 + (timedelta.seconds / 60 / 60)
    minute = (timedelta.seconds / 60 % 60)
    second = timedelta.seconds - minute * 60 - hours * 60 * 60

    return u"{0:01d}分{1:01d}秒".format(minute, second)
