# -*- coding: utf-8 -*-

import datetime
import random
import operator
import urllib

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.utils.importlib import import_module

from submodule.gu3.pager import get_pager
from submodule.gsocial.http import HttpResponseOpensocialRedirect
from submodule.gsocial import ActionRecord

from module.common.api_entity import get_entity
from module.common.api_event_entity import EVENT_TYPE_EVENT
from module.card.models import Card
from module.help.api import get_help_content, get_help_content_detail,get_help_content_detail_by_page
from module.battlelogic.genju_hime_chain_skill import get_chain_skill_seed_dict, convert_chain_skill_candidate_list
from module.battle.api import BATTLE_SIDE_ATTACK, get_battle_member_list
from module.bannerarrange.api import get_event_banner, get_active_gashapon_banner
from module.card.api import get_card, get_cards, get_special_skill_card_list
from module.player.decorators import require_player
from module.skill.api import get_skill
from module.weekdungeon.models import Dungeon
from module.rarity.models import Rarity
from module.raidgashapon.api import get_active_raid_gashapon
from module.playerraidgashapon.api import exist_ar_boss, exist_appeal_boss, get_appeal_boss_card_id
from module.campaign.api import get_campaign

from gachamodule.fgacha.api import get_gashapon, get_latest_coin_gashapon, get_gashapon_by_module,\
    get_active_gashapon_by_raidgashapon
from gachamodule.fgacha.models import GashaponAttentionCard

from eventmodule.ecommon.api import get_enable_event_by_id
from eventmodule import Event
from eventmodule.ecommon.api import get_enable_events
from eventmodule.ecommon.api import get_config
from gachamodule.fgacha.constants import C

TEMPLATE_PATH = 'help/'


@require_player
def help_index(request):
    '''
    ヘルプの一覧を取得します
    '''
    player = request.player
    help_title_list = get_help_content()
    page_html = TEMPLATE_PATH + 'index.html'
    from module.seek.api import HIDDEN_TYPE_HELP, is_not_found
    is_seek_event = is_not_found(player, HIDDEN_TYPE_HELP)
    
    testflg = False
    if player.pk in settings.MAINTENANCE_OSUSER_IDS:
        testflg = True
    
    ctxt = RequestContext(request, {
        'help_title_list': help_title_list,
        'is_seek_event': is_seek_event,
        'type': player.encryption(HIDDEN_TYPE_HELP),
        'testflg': testflg,
        'osuser_id': player.osuser_id,
        })

    return render_to_response(page_html, ctxt)


@require_player
def help_detail(request, help_id):
    help_title_list = get_help_content()
    length = len(help_title_list)

    help_info = get_help_content_detail(help_id)

    next_page = []
    if length > help_info.page:
        next_help_page = help_info.page + 1
        next_page = get_help_content_detail_by_page(next_help_page)

    page_html = TEMPLATE_PATH + 'detail.html'
    ctxt = RequestContext(request, {
        'help_info': help_info,
        'next_page': next_page,
        })

    return render_to_response(page_html, ctxt)


@require_player
def help_chain_skill(request):

    front, back, _, _ = get_battle_member_list(request.player, BATTLE_SIDE_ATTACK, is_max=True)
    seed_dict = get_chain_skill_seed_dict(front)
    candidate_list = convert_chain_skill_candidate_list(seed_dict)

    page_html = TEMPLATE_PATH + 'chain_skill.html'
    ctxt = RequestContext(request, {'candidate_list': candidate_list})
    return render_to_response(page_html, ctxt)


@require_player
def help_item_ice(request):

    page_html = TEMPLATE_PATH + 'item_ice.html'

    ctxt = RequestContext(request, {
        }
    )
    return render_to_response(page_html, ctxt)


@require_player
def help_rainbow_slime(request):

    page_html = TEMPLATE_PATH + 'rainbow_slime.html'

    ctxt = RequestContext(request, {
        'card1': get_card(36182011),
        'enable_tower_event': get_enable_event_by_id(31),  # 聖樹3が有効な間はクエストボタンを表示させるよ
    })
    return render_to_response(page_html, ctxt)


@require_player
def help_event_rainbow_slime(request):

    page_html = TEMPLATE_PATH + 'event_rainbow_slime.html'

    ctxt = RequestContext(request, {
        'card1': get_card(36182011),
        'enable_tower_event': get_enable_event_by_id(31),  # 聖樹3が有効な間はクエストボタンを表示させるよ
    })
    return render_to_response(page_html, ctxt)


@require_player
def help_skill_slime(request):

    page_html = TEMPLATE_PATH + 'skill_slime.html'

    ctxt = RequestContext(request, {
        'card1': get_card(23933011),
        'enable_tower_event': get_enable_event_by_id(31),  # 聖樹3が有効な間はクエストボタンを表示させるよ
    })
    return render_to_response(page_html, ctxt)


@require_player
def help_mini_fairy(request):

    page_html = TEMPLATE_PATH + 'mini_fairy.html'

    ctxt = RequestContext(request, {
        'card1': get_card(14952011),
        'enable_tower_event': get_enable_event_by_id(31),  # 聖樹5が有効な間はクエストボタンを表示させるよ
    })
    return render_to_response(page_html, ctxt)


@require_player
def help_special_material_card_list(request, card_id=None):

    special_card_ids = [36182011, 23933011, 23951011, 21954011]
    all_card_list = get_cards()

    strong_material_card_list = []
    high_price_material_card_list = []
    love_material_card_list = []

    for card in all_card_list:
        if card.pk in special_card_ids:
            continue

        if card.flag_is_love_up_material() or card.flag_is_love_max_material():
            love_material_card_list.append(card)
        elif card.flag_is_strong_material():
            strong_material_card_list.append(card)
        elif card.flag_is_high_price_material():
            high_price_material_card_list.append(card)

    special_card_list = [get_card(x) for x in special_card_ids]

    card_list = []
    card_list += strong_material_card_list + high_price_material_card_list + love_material_card_list + special_card_list

    if card_id:
        card_id = int(card_id)
        card = get_card(card_id)
    else:
        card = random.choice(card_list)

    love_material_card_list.sort(key=operator.attrgetter('id'), reverse=True)
    high_price_material_card_list.sort(key=operator.attrgetter('id'), reverse=True)
    strong_material_card_list.sort(key=operator.attrgetter('id'), reverse=True)

    ctxt = RequestContext(request, {
        'special_card_list': special_card_list,
        'strong_material_card_list': strong_material_card_list,
        'high_price_material_card_list': high_price_material_card_list,
        'love_material_card_list': love_material_card_list,
        'random_card': card,
        'card_list': card_list,
    })
    page_html = TEMPLATE_PATH + 'special_material_card_list.html'
    return render_to_response(page_html, ctxt)


@require_player
def axis_3(request):

    ctxt = RequestContext(request, {
        'card1': get_card(14295011),
        'enable_tower_event': get_enable_event_by_id(26),  # 不思議の国の幻夢姫が有効な間はクエストボタンを表示させるよ
    })
    page_html = TEMPLATE_PATH + 'axis_3.html'
    return render_to_response(page_html, ctxt)


@require_player
def limited_skill_description(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    event = Event(request).get_current_event()

    from module.item.api import get_item
    raid_gashapon = get_active_raid_gashapon()

    if raid_gashapon:
        if raid_gashapon.is_second_half():
            choice_cards_ids = [16805111, 26806111, 26807111, 36808111, 34812111]
            choice_cards = [get_card(x) for x in choice_cards_ids]
            ctxt_params = {
                'choice_cards': choice_cards,
                'event_banner': event_banner,
                'gashapon_banner': get_active_gashapon_banner(),
                'event': event,
            }
            pass

        elif raid_gashapon.is_middle_phase():
            choice_cards_ids = [16802111, 36804111, 26803111, 16805111, 26806111, 26807111, 36808111, 34812111, 34811111, 24810111, 14809111]
            choice_cards = [get_card(x) for x in choice_cards_ids]
            ctxt_params = {
                'choice_cards': choice_cards,
                'event_banner': event_banner,
                'gashapon_banner': get_active_gashapon_banner(),
                'event': event,
            }
            pass

        else:
            choice_cards_ids = [36861111, 26860111, 16857111, 14863111, 24864111, 34865111]
            choice_cards = [get_card(x) for x in choice_cards_ids]
            ctxt_params = {
                'choice_cards': choice_cards,
                'event_banner': event_banner,
                'gashapon_banner': get_active_gashapon_banner(),
                'event': event,
            }
            #del ctxt_params['card3']
            pass
    else:

        ctxt_params = {
            'event_banner': event_banner,
            'gashapon_banner': get_active_gashapon_banner(),
            'event': event,
        }

    ctxt_params.update({'raid_gashapon': raid_gashapon})

    ctxt = RequestContext(request, ctxt_params)
    page_html = TEMPLATE_PATH + 'limited_skill_description.html'
    return render_to_response(page_html, ctxt)


@require_player
def new_princess(request, select_new_card_id=None):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    event = Event(request).get_current_event()
    raid_gashapon = get_active_raid_gashapon()

    gashapon = get_latest_coin_gashapon()
    attention_card_list = GashaponAttentionCard.get_attention_card_list(gashapon.id)
    choice_cards = [ac.card for ac in attention_card_list]
    choice_card_ids = [card.pk for card in choice_cards]
    choice_card = choice_cards[0]
    if select_new_card_id:
        choice_card = [x for x in choice_cards if x.id == int(select_new_card_id)][0]

    events = get_enable_events()
    if events:
        event = events[-1]
        event_boss_model = None
        try:
            event_boss_model = import_module('eventmodule.{}.boss_models'.format(event.module))
        except ImportError:
            pass

        tmp_choice_card_ids = []
        for choice_card_id in choice_card_ids:
            rank_minus = choice_card_id % 10
            if rank_minus == 3:
                tmp_choice_card_ids.append(choice_card_id)
                tmp_choice_card_ids.append(choice_card_id - 1)
                tmp_choice_card_ids.append(choice_card_id - 2)
            elif rank_minus == 1:
                tmp_choice_card_ids.append(choice_card_id)
                tmp_choice_card_ids.append(choice_card_id + 1)
                tmp_choice_card_ids.append(choice_card_id + 2)
            elif rank_minus == 2:
                tmp_choice_card_ids.append(choice_card_id)
                tmp_choice_card_ids.append(choice_card_id + 1)
                tmp_choice_card_ids.append(choice_card_id - 1)

        choice_card_ids = list(set(tmp_choice_card_ids))

        killer_card_rates = {}
        for killer_card in event_boss_model.KillerCard.get_cache_all():
            if killer_card.card_id not in choice_card_ids:
                continue

            if killer_card.card_id not in killer_card_rates:
                killer_card_rates[killer_card.card_id] = {'atk': 0, 'ptx': 0}

            if killer_card.killer_type == event_boss_model.KillerCard.ATTACK and killer_card.factor != 999:
                if killer_card.factor > killer_card_rates[killer_card.card_id]['atk']:
                    killer_card_rates[killer_card.card_id]['atk'] = killer_card.factor

            elif killer_card.killer_type == event_boss_model.KillerCard.POINT:
                if killer_card.factor > killer_card_rates[killer_card.card_id]['ptx']:
                    killer_card_rates[killer_card.card_id]['ptx'] = killer_card.factor

        for choice_card_tmp in choice_cards:
            choice_card_tmp_id = choice_card_tmp.pk
            if choice_card_tmp_id in killer_card_rates:
                choice_card_tmp.max_atk_up = killer_card_rates[choice_card_tmp_id]['atk']
                choice_card_tmp.max_ptx_up = killer_card_rates[choice_card_tmp_id]['ptx']
            choice_card_tmp_id += 1
            if choice_card_tmp_id in killer_card_rates:
                if choice_card_tmp.max_atk_up < killer_card_rates[choice_card_tmp_id]['atk']:
                    choice_card_tmp.max_atk_up = killer_card_rates[choice_card_tmp_id]['atk']
                if choice_card_tmp.max_ptx_up < killer_card_rates[choice_card_tmp_id]['ptx']:
                    choice_card_tmp.max_ptx_up = killer_card_rates[choice_card_tmp_id]['ptx']
            choice_card_tmp_id += 1
            if choice_card_tmp_id in killer_card_rates:
                if choice_card_tmp.max_atk_up < killer_card_rates[choice_card_tmp_id]['atk']:
                    choice_card_tmp.max_atk_up = killer_card_rates[choice_card_tmp_id]['atk']
                if choice_card_tmp.max_ptx_up < killer_card_rates[choice_card_tmp_id]['ptx']:
                    choice_card_tmp.max_ptx_up = killer_card_rates[choice_card_tmp_id]['ptx']


    ctxt_params = {
        'choice_cards': choice_cards,
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
        'event': event,
        'choice_card': choice_card,
    }

    if raid_gashapon:
        active_raid_gashapons = raid_gashapon.get_active_schedule()
        image_raid_gashapon_id = active_raid_gashapons[0].id

        raid_gashapon_first = get_active_gashapon_by_raidgashapon()

        is_exist_ar_boss = exist_ar_boss(raid_gashapon.id)
        is_exist_appeal_boss = exist_appeal_boss(raid_gashapon.id)

        appeal_card = None

        ctxt_params.update({
            'C': C(raid_gashapon_first),
            'raid_gashapon': raid_gashapon,
            'exist_ar_boss': is_exist_ar_boss,
            'exist_appeal_boss': is_exist_appeal_boss,
            'image_raid_gashapon_id': image_raid_gashapon_id,
        })

        if is_exist_ar_boss:
            ctxt_params.update({
                'top_ani_pri_voice': attention_card_list[0].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'top_pri_voice': attention_card_list[1].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'left_pri_voice': attention_card_list[2].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                #'right_pri_voice': attention_card_list[3].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'appeal_pri_voice':None,
            })
        elif is_exist_appeal_boss:
            appeal_boss_card_id = get_appeal_boss_card_id(raid_gashapon.id)
            appeal_boss_card = get_card(appeal_boss_card_id)

            ctxt_params.update({
                'top_ani_pri_voice': None,
                'top_pri_voice': attention_card_list[0].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'left_pri_voice': attention_card_list[1].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'right_pri_voice': attention_card_list[2].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'appeal_pri_voice': appeal_boss_card.detail.voice_url_by_id(random.choice(range(1, 15))),
            })
        else:
            ctxt_params.update({
                'top_ani_pri_voice': None,
                'top_pri_voice': attention_card_list[0].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'left_pri_voice': attention_card_list[1].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'right_pri_voice': attention_card_list[2].card.detail.voice_url_by_id(random.choice(range(1, 15))),
                'appeal_pri_voice':None,
            })
    ctxt = RequestContext(request, ctxt_params)
    page_html = TEMPLATE_PATH + 'new_princess.html'
    return render_to_response(page_html, ctxt)


@require_player
def rarity_new_princess(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    now = datetime.datetime.now()
    limit = datetime.datetime(2013, 02, 27, 16, 00, 00)
    rest_time = limit - now
    seconds = rest_time.total_seconds()
    hh = int(seconds / 3600)
    mm = int(seconds % 3600 / 60)
    ss = int(seconds % 60)
    rest_time = u'%d時間%02d分%02d秒' % (hh, mm, ss)
    ctxt = RequestContext(request, {
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
        'rest_time': rest_time,
    })
    page_html = TEMPLATE_PATH + 'rarity_new_princess.html'
    return render_to_response(page_html, ctxt)


@require_player
def soul_seed_pr(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'soul_seed_pr.html'
    return render_to_response(page_html, ctxt)


@require_player
def card_explanation(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'random_card': get_card(17542011),

        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'card_explanation.html'
    return render_to_response(page_html, ctxt)


@require_player
def skill_level_up(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'skill_level_up.html'
    return render_to_response(page_html, ctxt)


@require_player
def card_introduction(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'card1': get_card(26634011),
        'card2': get_card(36633011),
        'card3': get_card(14635011),
        'card4': get_card(34636011),
        'card5': get_card(24637011),
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'card_introduction.html'
    return render_to_response(page_html, ctxt)


@require_player
def notice_event_guild(request):
    player = request.player
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    mood_body = None
    mood_callbackurl = None
    kvs = player.get_kvs('event_notice_mood')
    if not kvs.get():
        abs_url = lambda url_name, args=(), kwargs={}: 'http://%s%s' % (settings.SITE_DOMAIN, reverse(url_name, args=args, kwargs=kwargs))
        mood_body = mood_callbackurl = None
        mood_body = u'<a href="http://pf.gree.net/55446">幻獣姫でｷﾞﾙﾄﾞ対抗ｲﾍﾞﾝﾄが始まるみたい!ｲﾍﾞﾝﾄ限定姫が手に入るかも♪今ならﾛｸﾞｲﾝで特別Sﾚｱ姫がもらえるよ!美麗姫を服従・調教・昇天させよ♪</a>'
        mood_callbackurl = urllib.quote(abs_url('help_mood_callback'))
        if not request.is_smartphone:
            mood_body = mood_body.replace('pf.gree.net', 'mpf.gree.jp')

    ctxt = RequestContext(request, {
        'card1': get_card(25708011),
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
        'mood_body': mood_body,
        'mood_callbackurl': mood_callbackurl,
    })
    page_html = TEMPLATE_PATH + 'notice_event_guild.html'
    return render_to_response(page_html, ctxt)


@require_player
def mood_callback(request):
    player = request.player
    kvs = player.get_kvs('event_notice_mood')
    if not kvs.get():
        from module.gift.api import npc_give_gift
        npc_give_gift(player.pk, settings.ENTITY_TYPE_ITEM, 207, 1, u'{}のひとこと送信によるお礼だよ♪'.format(u'ｲﾍﾞﾝﾄ予告'))
        kvs.set(1)
    return HttpResponseOpensocialRedirect(reverse('notice_event_guild'))


@require_player
def special_skill_explanation(request, skill_id=None, page=1):
    event = Event(request).get_current_event()
    now = datetime.datetime.now()

    '''
    # グリーにカードをさされたので一旦非表示にするカードとスキルのリスト
    1000185 神姫創造（37877111, 37877112, 37877113）
    1000124 ﾊｰﾄ･ｵﾌﾞ･ｴﾝｼｪﾝﾄ（17674111, 17675113, 27682111, 27683113, 37690111, 37691113）
    1000111 雷鳴と電光（27326111, 27326112, 27326113）
    1000004 進撃の一撃（27732011, 27732012, 27732013）※別姫も所持。表示削除はバハムートのみ
    1000128 ｺｽﾓ･ﾎﾞﾃﾞｨ（17701111, 17701112, 17701113, 27702111, 27702112, 27702113, 37703111, 37703112, 37703113）
    1000219 26974111, 26974112, 26974113
    '''
    if settings.IS_GREE:
        exclude_card_id_list = [37877111, 37877112, 37877113, 17674111, 17675113, 27682111, 27683113, 37690111, 37691113, 27326111, 27326112, 27326113, 27732011, 27732012, 27732013, 17701111, 17701112, 17701113, 27702111, 27702112, 27702113, 37703111, 37703112, 37703113, 26974111, 26974112, 26974113]
        exclude_skill_id_list = [1000185, 1000124, 1000111, 1000004, 1000128, 1000219]
    else:
        exclude_card_id_list = []
        exclude_skill_id_list = []

    if skill_id in exclude_skill_id_list:
        return HttpResponseOpensocialRedirect(reverse('thanks_money'))

    skill_img = False
    skilL_sample_link = False

    now = datetime.datetime.now()

    gashapon = get_latest_coin_gashapon()
    card4 = False
    card5 = False
    card6 = False

    pr_card_list = [x for x in Card.get_cache_all() if x.rarity >= Rarity.PRINCESS_RARE and x.chain_skill_2_id > 0]
    pr_card_list = [x for x in pr_card_list if not x.id in exclude_card_id_list]
    temp_pr_card_list = pr_card_list
    pr_card_list = []
    for pr_card in temp_pr_card_list:
        if pr_card.release_date and now <= pr_card.release_date:
            continue
        pr_card_list.append(pr_card)
    pr_choice_card_list = random.sample(pr_card_list, 2)

    card1 = pr_choice_card_list[0]
    card2 = pr_choice_card_list[1]

    if gashapon and gashapon.is_enable:

        from gachamodule.fgacha.constants import C
        from gachamodule.fgacha.models import GashaponAttentionCard

        attention_card_list = GashaponAttentionCard.get_attention_card_list(gashapon.id)
        attention_card_list = [x for x in attention_card_list if getattr(x.card, 'chain_skill_2_id')]
        if len(attention_card_list) > 1:
            choice_card_list = [ac.card for ac in attention_card_list if ac.card and ac.card.rarity >= Rarity.SUPER_RARE]
            choice_card_list = [x for x in choice_card_list if not x.id in exclude_card_id_list]

            if len(choice_card_list) > 1:
                sample_card_list = random.sample(choice_card_list, 2)
                card1 = sample_card_list[0]
                card2 = sample_card_list[1]
            elif card1:
                card2 = random.choice(choice_card_list)
            else:
                card1 = random.choice(choice_card_list)

            luckygashapon = get_gashapon_by_module('luckygacha')
            if luckygashapon and (luckygashapon.begin_at <= datetime.datetime.now() and luckygashapon.end_at >= datetime.datetime.now()):
                if C(luckygashapon).SPECIAL_CARD:
                    card1 = C(luckygashapon).SPECIAL_CARD

    skill = get_skill(card1.chain_skill_2_id)
    card1_skill_name = skill.name
    card1_sukill_description = skill.description
    skill_img = False
    card1_next_event_flag = False
    skilL_sample_link = False

    #基本的にｲﾍﾞﾝﾄでﾗﾝｷﾝｸﾞ報酬の姫
    skill = get_skill(card2.chain_skill_2_id)
    skill_img2 = False
    card2_skill_name = skill.name
    card2_sukill_description = skill.description
    card2_next_event_flag=False

    card3 = False
    skill_img3 = False
    card3_skill_name = False
    card3_sukill_description = False
    skill_img_3 = False
    card3_next_event_flag = False

    card4 = False
    card5 = False
    card6 = False

    skill_img3 = False
    skill_img4 = False

    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    pager = None

    special_skill = None

    if skill_id:
        skill_id = int(skill_id)
        special_skill = get_skill(skill_id)

    card_list = get_special_skill_card_list()
    card_list = [x for x in card_list if not x.id in exclude_card_id_list]
    event_skill_cards = {}

    special_skill_list = []

    for card in card_list:
        if card.release_date and now <= card.release_date:
            continue
        if card.rank == 1 or card.chain_skill_2_id in [1000153, 1000154, 1000155]:  # ｳｫｰﾙ・ｱﾄﾗｽだけはランク関係なく艶技がある
            special_skill_list.append(card.chain_skill_2)
            if skill_id and skill_id != card.chain_skill_2_id:
                continue
            if not event_skill_cards.has_key(card.chain_skill_2):
                event_skill_cards[card.chain_skill_2] = []

            event_skill_cards[card.chain_skill_2].append(card)

    special_skill_list = list(set(special_skill_list))
    special_skill_list = [x for x in special_skill_list if x.id not in exclude_skill_id_list]

    # イベント、曜日別ダンジョンで発動禁止フラグあれば省く
    special_skill_list = [x for x in special_skill_list if not x.flag_can_not_invoke_on_event()]
    special_skill_list = [x for x in special_skill_list if not x.flag_can_not_invoke_on_weekdungeon()]

    pager, special_skill_list = get_pager(special_skill_list, 10, page=page)

    ctxt = RequestContext(request, {
        'now': now,
        'event': event,
        'card1': card1,
        'card1_skill_name': card1_skill_name,
        'card1_sukill_description': card1_sukill_description,
        'skill_img' : skill_img,
        'card1_next_event_flag' : card1_next_event_flag,
        'card2': card2,
        'card2_skill_name': card2_skill_name,
        'card2_sukill_description': card2_sukill_description,
        'skill_img2' : skill_img2,
        'card2_next_event_flag' : card2_next_event_flag,
        'card3': card3,
        'skill_img3' : skill_img3,
        'card3_skill_name': card3_skill_name,
        'card3_sukill_description': card3_sukill_description,
        'skill_img_3' : skill_img_3,
        'card3_next_event_flag' : card3_next_event_flag,
        'card4' : card4,
        'card5' : card5,
        'card6' : card6,
        'event_skill_cards':event_skill_cards,
        'special_skill_list': special_skill_list,
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
        'skill_id': skill_id,
        'special_skill' : special_skill,
        'skilL_sample_link' : skilL_sample_link,
        'pager': pager,
    })
    page_html = TEMPLATE_PATH + 'special_skill_explanation.html'
    return render_to_response(page_html, ctxt)

@require_player
def function_will(request, page=1):
    from module.adventbox.api import get_active_advent_box
    from module.loginbonus.api import get_login_stamp
    from module.raidgashapon.api import get_active_raid_gashapon
    if settings.IS_GREE:
        campaign_id = 3
        login_stamp = get_login_stamp(17)
        raid_gashapon = get_active_raid_gashapon()
    elif settings.IS_MBGA:
        campaign_id = 2
        login_stamp = get_login_stamp(17)
        raid_gashapon = get_active_raid_gashapon()
    else:
        campaign_id = 2
        login_stamp = get_login_stamp(26)
        raid_gashapon = get_active_raid_gashapon()

    campaign = get_campaign(campaign_id)

    def is_enable_campaign(campaign):
        now = datetime.datetime.now()

        # オープンが未来の場合True
        if campaign.begin_at and now < campaign.begin_at:
            return True
        else:
            return campaign.enable
        return False

    # 月初raid_gashaponの場合はTure
    is_active_battle_gacha = False
    if raid_gashapon:
        if raid_gashapon.is_first_half() or raid_gashapon.is_middle_phase():
            is_active_battle_gacha = True

    ctxt = RequestContext(request, {
        'gashapon_banner': get_active_gashapon_banner(),
        'page': page,
        'adventbox': get_active_advent_box(),
        'login_stamp': login_stamp,
        'campaign_enable': is_enable_campaign(campaign),
        'login_stamp_enable': is_enable_campaign(login_stamp),
        'is_active_battle_gacha': is_active_battle_gacha,
    })
    page_html = TEMPLATE_PATH + 'function_will.html'
    return render_to_response(page_html, ctxt)


@require_player
def million_notice(request):
    if settings.IS_GREE:
        gashapon_id = 610
        campaign_id = 3
    elif settings.IS_MBGA:
        gashapon_id = 253
        campaign_id = 2
    else:
        gashapon_id = 254
        campaign_id = 2

    # ボスバトルは後半戦になっていたら期間終了
    gashapon = get_gashapon(gashapon_id)
    const = C(gashapon)

    is_finshed_battle_gacha = not const.is_middle_phase()

    campaign = get_campaign(campaign_id)
    now = datetime.datetime.now()
    campaign_enable = False

    # オープンが未来の場合True
    if campaign.begin_at and now < campaign.begin_at:
        campaign_enable = True
    else:
        campaign_enable = campaign.enable

    ctxt = RequestContext(request, {
        'is_finshed_battle_gacha': is_finshed_battle_gacha,
        'campaign_enable': campaign_enable,
    })
    page_html = TEMPLATE_PATH + 'breakthrough_campaign.html'
    return render_to_response(page_html, ctxt)


@require_player
def campaign_3th(request):
    campaign_state = []
    now = datetime.datetime.now()
    # ログインボーナス
    campaign_state.append(now <= datetime.datetime(2015, 6, 9, 23, 59, 59))
    # トウテツ登場
    campaign_state.append(now <= datetime.datetime(2015, 6, 9, 11, 59, 59))
    # 調教大成功
    campaign_state.append(now <= datetime.datetime(2015, 6, 9, 11, 59, 59))
    # 人気投票結果
    campaign_state.append(now <= datetime.datetime(2015, 6, 9, 11, 59, 59))

    ctxt = RequestContext(request, {
        'campaign_state': campaign_state,
    })
    return render_to_response(TEMPLATE_PATH + 'campaign_3th.html', ctxt)

@require_player
def aprilfool_campaign(request):
    if settings.IS_GREE:
        loginstamp_id = 784
    elif settings.IS_MBGA:
        loginstamp_id = 358
    elif settings.IS_DGAME:
        loginstamp_id = 352
    else:
        loginstamp_id = 0

    from module.loginbonus.models import LoginBonus
    login_bonus = LoginBonus.get_cache(loginstamp_id)

    if login_bonus is None:
        return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

    from eventmodule.ecommon.api import get_event
    from eventmodule.ecommon.importlib import models
    event = get_event(119)
    boss = models(event.id).Boss.get_cache(1)

    from module.bannerarrange.api import get_banner_tag, get_active_arrange_list
    from module.bannerarrange.models import ArrangeBase
    banner_list = get_active_arrange_list()
    event_banner = [x for x in banner_list if
                    x.get_banner().event_type == EVENT_TYPE_EVENT and
                    x.get_banner().event_id == event.id]

    if event_banner:
        event_banner_tag = get_banner_tag(ArrangeBase.MYPAGE_MIDDLE, event_banner)[0]
    else:
        event_banner_tag = None

    ctxt = RequestContext(request, {
        'campaign_title': u'ﾋﾞｯｸﾞｶﾞﾝｶﾞﾝ',
        'campaign_name': login_bonus.name,
        'begin_at': login_bonus.begin_at,
        'end_at': login_bonus.end_at,
        'card': get_entity(login_bonus.entity_type, login_bonus.entity_id),
        'quantity': login_bonus.quantity,
        'event_banner_tag': event_banner_tag,
        'target_boss': boss,
        'target_event': event,
    })

    page_html = TEMPLATE_PATH + u'aprilfool_campaign.html'
    return render_to_response(page_html, ctxt)

@require_player
def boss_battle_sample_production(request):
    from module.common.deviceenvironment.device_environment import media_root
    from module.misc.view_utils import render_swf_mapping
    from module.card.api import get_card
    from module.skill.api import get_special_skill_text_params
    from eventmodule.ecommon.api import get_event
    raid_gashapon = get_active_raid_gashapon()
    gashapon = get_latest_coin_gashapon()

    player = request.player
    next_url = reverse('fgacha_index')
    event = None
    if raid_gashapon and raid_gashapon.is_middle_phase():
        event = get_event(114)
    else:
        event = get_event(114)
    if not event:
        return HttpResponseOpensocialRedirect(reverse('fgacha_index'))

    if event:
        from eventmodule.grow_raid.boss_models import Boss
        boss = Boss.get_cache(3)
        swf_id_mapper = __import__('{}.swf_id_mapper'.format(event.module), fromlist=['eventmodule'])
        if get_config(player).get_simple_flash() and not request.is_smartphone:
            swf_filename = 'event/common/raid_battle_2'
            id_mapper = getattr(swf_id_mapper, 'swf_mapping_raid_battle_{}_2'.format(event.module))
        else:
            swf_filename = 'event/{}/raid_battle'.format(event.resource_path)
            id_mapper = getattr(swf_id_mapper, 'swf_mapping_raid_battle_{}'.format(event.module))

        if settings.IS_GREE:
            if raid_gashapon and raid_gashapon.is_middle_phase():
                card1 = get_card(25378213)
                card2 = get_card(27412213)
                card3 = get_card(17390213)
                card4 = get_card(37413213)
                card5 = get_card(26414213)
                card6 = get_card(36417213)
                card7 = get_card(16416213)
                card8 = get_card(26419213)
                card9 = get_card(36418213)
                card10 = get_card(27411213)

                params = {
                    'SoulBonusColor': u'',
                    'SoulBonusPlayer': u'',
                    'SoulBonusPower': u'',
                    'SoulBonusTxt': u'',
                    'abs7Name': u'魅惑の奈落',
                    'abs7Txt': u'極致的攻撃&自分全回復!!',
                    'angTurnTxt': u'怒ってます！',
                    'artKillName': u'朔望圧縮',
                    'artKillTxt': u'超絶大攻撃&条件達成で即死確率上昇',
                    'bMissTxt': u'おしい…!!失敗した',
                    'bindEndTxt': u'麻痺がとけた!!',
                    'bindTurnTxt': u'麻痺して動くことができない',
                    'bossAttackPattern': u':::',
                    'bossDamage_a': u'111700962',
                    'bossHpMax_a': u'99999999',
                    'bossHp_a': u'99999999',
                    'bossTypeNum': u'1',
                    'brr1_5Name': u'金光頑健',
                    'brr1_5Txt': u'ボスの攻撃を3ターン無効化!',
                    'burnEndTxt': u'やけどが治った',
                    'burnTurnTxt': u'やけどのﾀﾞﾒｰｼﾞを受けている',
                    'cMissTxt': u'ﾊｽﾞしてしまった…',
                    'charPassType': u'1',
                    'criG1Name': u'輝く雑草',
                    'criG1Txt': u'超絶攻撃+敵のHPを割合で削る',
                    'darkEndTxt': u'敵を覆う闇が消えた!!',
                    'endTxt': u'戦闘に勝利した!!',
                    'enterBossTxt': u'[情熱]真極･激昂の火焔姫の襲撃！',
                    'fort2TurnTxt': u'姫の怒りがおさまらない!!',
                    'fortTurnTxt': u'激しい焔が敵を襲う!!',
                    'guildHime': u'0',
                    'helpFlg': u'0',
                    'hpEnd': u'100,100,100,100,100,100,100,100,100,100',
                    'hpStart': u'100,100,100,100,100,100,100,100,100,100',
                    'iMissTxt': u'残念…敵のﾔﾙ気を削る事に失敗した!',
                    'immEndTxt': u'敵がﾔﾙ気を取り戻した!気をつけよう!',
                    'immTurnTxt': u'敵は攻撃する気がないようだ!',
                    'killMissTxt': u'即死効果は失敗した!',
                    'limitTurnNum': u'1',
                    'mRnd3Name': u'太陽を追いしもの',
                    'mRnd3Txt': u'敵に5〜8回のﾗﾝﾀﾞﾑ中攻撃!',
                    'mag1NameE': u'悪の波動',
                    'mag1TxtE': u'全体に特大ﾀﾞﾒｰｼﾞ!!',
                    'magBurn5Dmg_a': u'999999',
                    'magBurn5Name': u'放蕩炮烙',
                    'magBurn5Turn': u'3',
                    'magBurn5Txt': u'極大攻撃+確率で3ﾀｰﾝ敵をやけどに!',
                    'magHeal2Name': u'ｳｨｽﾞ･ﾌｧｰｽﾃｨｽ',
                    'magHeal2Txt': u'敵を極大攻撃後、味方全員小回復',
                    'onIcon': u'1,1,1,1,1,1,1,1,1,1',
                    'openingTxt': u'[情熱]真極･激昂の火焔姫の襲撃！',
                    'p10_atLst': u'24495620:abs7::100::1',
                    'p10_hpLst': u'',
                    'p1_atLst': u'428700:tornadoImm:a:::1',
                    'p1_hpLst': u'',
                    'p2_atLst': u'11753962_miss:titaKill2::::1',
                    'p2_hpLst': u'',
                    'p3_atLst': u'1228200_8658913:criG1::::1',
                    'p3_hpLst': u'',
                    'p4_atLst': u'44456020_miss:artKill::::1',
                    'p4_hpLst': u'',
                    'p5_atLst': u'2318337:rinp7::::1',
                    'p5_hpLst': u'',
                    'p6_atLst': u'7328850:magHeal2:6:100::1',
                    'p6_hpLst': u'',
                    'p7_atLst': u'3998800:magBurn5:a:::1',
                    'p7_hpLst': u'',
                    'p8_atLst': u':brr1_5:9:::1',
                    'p8_hpLst': u'',
                    'p9_atLst': u'1172260_1172260_1172260_1172260_1172260_1172260:mRnd3::::1',
                    'p9_hpLst': u'',
                    'playerNum': u'1234567890',
                    'psnEndTxt': u'毒の効果がきれたようだ…!!',
                    'psnTurnTxt': u'毒のﾀﾞﾒｰｼﾞを受けている',
                    'regTurnTxt': u'毎ﾀｰﾝHP回復!',
                    'revMissTxt': u'おしい…!!失敗した',
                    'rinp7Name': u'月と魔術と贖罪と',
                    'rinp7Txt': u'敵全体に攻撃+確率で命中率ﾀﾞｳﾝ!',
                    'skTxt1': u'1,1235780,[攻撃上昇]ｱﾀﾞﾙﾄ･ﾎﾞﾃﾞｨ,情熱・妖艶ﾀｲﾌﾟの攻撃 極大ｱｯﾌﾟ',
                    'skTxt2': u'3,37,ﾒﾃｵ･ﾌﾚｱ,情熱ﾀｲﾌﾟの攻防 超絶ｱｯﾌﾟ',
                    'skTxt3': u'5,5,幻視の黙示,自分の攻防 極大ｱｯﾌﾟ',
                    'skTxt4': u'12580,12580,[連携]神秘ﾎﾞﾃﾞｨ,妖艶ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt5': u'469,469,[連携]無垢ﾎﾞﾃﾞｨ,清純ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt6': u'570,570,[連携]蠢くﾀﾞｰｸﾈﾋﾞｭﾗ,闇属性の攻防 小ｱｯﾌﾟ',
                    'skillIcon': u'1111111111',
                    'skillNum': u'6',
                    'stlHitTxt': u'強奪に成功した!!',
                    'stlHitTxt_a': u'強奪に成功した!!',
                    'stlHitTxt_b': u'強奪に成功した!!',
                    'stlHitTxt_c': u'強奪に成功した!!',
                    'stlMissTxt': u'無念!強奪に失敗した…',
                    'success': u'1',
                    'timeBonusTxt1': u'',
                    'timeBonusTxt2': u'',
                    'titaKill2Name': u'一緒に踊りましょ♪',
                    'titaKill2Txt': u'敵に超絶大攻撃&確率で即死!',
                    'tokkouBonusColor': u'0,2,0,2,1,1,1,1,1,2,',
                    'tokkouBonusPlayer': u'1,2,3,4,5,6,7,8,9,10,',
                    'tokkouBonusPower': u'2,24,2,24,12,12,12,12,12,36,',
                    'tokkouBonusTxt': u'秘められた力が解放!',
                    'tornadoImmName': u'羽団扇一閃',
                    'tornadoImmTxt': u'極大攻撃+確率で敵が攻撃してこない!',
                    'useBP': u'3',
                    'winHp0': u'0',
                }
            else:
                card1 = get_card(27412213)
                card2 = get_card(16416213)
                card3 = get_card(27398213)
                card4 = get_card(36417213)
                card5 = get_card(26419213)
                card6 = get_card(25378213)
                card7 = get_card(36379213)
                card8 = get_card(34420213)
                card9 = get_card(14423213)
                card10 = get_card(27411213)

                params = {
                    'SoulBonusColor': u'',
                    'SoulBonusPlayer': u'',
                    'SoulBonusPower': u'',
                    'SoulBonusTxt': u'',
                    'abs2Name': u'ﾌﾞﾗｯﾃﾞｨ・ﾚｲﾝ',
                    'abs2Txt': u'敵を攻撃&自分中回復!!',
                    'abs7Name': u'魅惑の奈落',
                    'abs7Txt': u'極致的攻撃&自分全回復!!',
                    'angTurnTxt': u'怒ってます！',
                    'bMissTxt': u'おしい…!!失敗した',
                    'bindEndTxt': u'麻痺がとけた!!',
                    'bindTurnTxt': u'麻痺して動くことができない',
                    'bossAttackPattern': u'8:2:4:5',
                    'bossDamage_a': u'149883425',
                    'bossHpMax_a': u'99999999',
                    'bossHp_a': u'99999999',
                    'bossTypeNum': u'3',
                    'brr1_5Name': u'金光頑健',
                    'brr1_5Txt': u'ボスの攻撃を3ターン無効化!',
                    'burnEndTxt': u'やけどが治った',
                    'burnTurnTxt': u'やけどのﾀﾞﾒｰｼﾞを受けている',
                    'cMissTxt': u'ﾊｽﾞしてしまった…',
                    'charPassType': u'1',
                    'criG1Name': u'輝く雑草',
                    'criG1Txt': u'超絶攻撃+敵のHPを割合で削る',
                    'darkEndTxt': u'敵を覆う闇が消えた!!',
                    'endTxt': u'戦闘に勝利した!!',
                    'enterBossTxt': u'[清純]真極･激昂の火焔姫の襲撃！',
                    'fort2TurnTxt': u'姫の怒りがおさまらない!!',
                    'fortTurnTxt': u'激しい焔が敵を襲う!!',
                    'guildHime': u'0',
                    'helpFlg': u'0',
                    'hpEnd': u'100,73,100,73,73,100,100,100,100,100',
                    'hpStart': u'100,100,100,100,100,100,100,100,100,100',
                    'iMissTxt': u'残念…敵のﾔﾙ気を削る事に失敗した!',
                    'immEndTxt': u'敵がﾔﾙ気を取り戻した!気をつけよう!',
                    'immTurnTxt': u'敵は攻撃する気がないようだ!',
                    'killMissTxt': u'即死効果は失敗した!',
                    'limitTurnNum': u'1',
                    'mag1NameE': u'悪の波動',
                    'mag1TxtE': u'全体に特大ﾀﾞﾒｰｼﾞ!!',
                    'magBurn5Name': u'放蕩炮烙',
                    'magBurn5Turn': u'3',
                    'magBurn5Txt': u'極大攻撃+確率で3ﾀｰﾝ敵をやけどに!',
                    'magHeal2Name': u'ｳｨｽﾞ･ﾌｧｰｽﾃｨｽ',
                    'magHeal2Txt': u'敵を極大攻撃後、味方全員小回復',
                    'onIcon': u'1,1,1,1,1,1,1,0,0,1',
                    'openingTxt': u'[清純]真極･激昂の火焔姫の襲撃！',
                    'p10_atLst': u'87487840:abs7::100::1',
                    'p10_hpLst': u'',
                    'p1_atLst': u'46442287_miss:titaKill2::::1',
                    'p1_hpLst': u'',
                    'p2_atLst': u'1901575:magBurn5::::1',
                    'p2_hp': u'',
                    'p2_hpLst': u':73::',
                    'p3_atLst': u'2401200_4925493:criG1::::1',
                    'p3_hpLst': u'',
                    'p4_atLst': u'4213837:magHeal2:4:100::1',
                    'p4_hp': u'',
                    'p4_hpLst': u'::73:',
                    'p5_atLst': u':brr1_5:8:::1',
                    'p5_hp': u'73',
                    'p5_hpLst': u':::73',
                    'p6_atLst': u'1646325:tornadoImm::::1',
                    'p6_hpLst': u'',
                    'p7_atLst': u'164590:abs2::100::1',
                    'p7_hpLst': u'',
                    'p8_atLst': u'541810',
                    'p8_hp': u'100',
                    'p8_hpLst': u'100:::',
                    'p9_atLst': u'158468:c',
                    'p9_hpLst': u'',
                    'playerNum': u'1234567890',
                    'psnEndTxt': u'毒の効果がきれたようだ…!!',
                    'psnTurnTxt': u'毒のﾀﾞﾒｰｼﾞを受けている',
                    'regTurnTxt': u'毎ﾀｰﾝHP回復!',
                    'revMissTxt': u'おしい…!!失敗した',
                    'skTxt1': u'3,13560,爆裂滅光弾,妖艶ﾀｲﾌﾟの攻防 超絶ｱｯﾌﾟ',
                    'skTxt2': u'1,1234567890,[攻撃上昇]ﾊﾟﾗﾀﾞｲｽ･ﾛｽﾄ,全ﾀｲﾌﾟの攻撃 超絶ｱｯﾌﾟ',
                    'skTxt3': u'2,2,幻視の黙示,自分の攻防 極大ｱｯﾌﾟ',
                    'skTxt4': u'13560,13560,[連携]神秘ﾎﾞﾃﾞｨ,妖艶ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt5': u'4689,4689,[連携]乱心のﾃﾝﾍﾟｽﾄ,風属性の攻防 小ｱｯﾌﾟ',
                    'skTxt6': u'478,478,[連携]無垢ﾎﾞﾃﾞｨ,清純ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skillIcon': u'1111111001',
                    'skillNum': u'6',
                    'stlHitTxt': u'強奪に成功した!!',
                    'stlHitTxt_a': u'強奪に成功した!!',
                    'stlHitTxt_b': u'強奪に成功した!!',
                    'stlHitTxt_c': u'強奪に成功した!!',
                    'stlMissTxt': u'無念!強奪に失敗した…',
                    'success': u'1',
                    'timeBonusTxt1': u'',
                    'timeBonusTxt2': u'',
                    'titaKill2Name': u'一緒に踊りましょ♪',
                    'titaKill2Txt': u'敵に超絶大攻撃&確率で即死!',
                    'tokkouBonusColor': u'2,1,0,1,1,0,0,0,0,2,',
                    'tokkouBonusPlayer': u'1,2,3,4,5,6,7,8,9,10,',
                    'tokkouBonusPower': u'24,12,2,12,12,2,2,7,7,36,',
                    'tokkouBonusTxt': u'秘められた力が解放!',
                    'tornadoImmName': u'羽団扇一閃',
                    'tornadoImmTxt': u'極大攻撃+確率で敵が攻撃してこない!',
                    'useBP': u'3',
                    'winHp0': u'0',
                }
        else:
            if raid_gashapon and raid_gashapon.is_middle_phase():
                card1 = get_card(25378213)
                card2 = get_card(26419213)
                card3 = get_card(17390213)
                card4 = get_card(36418213)
                card5 = get_card(36417213)
                card6 = get_card(16416213)
                card7 = get_card(26414213)
                card8 = get_card(37413213)
                card9 = get_card(27412213)
                card10 = get_card(27411213)

                params = {
                    'SoulBonusColor': u'',
                    'SoulBonusPlayer': u'',
                    'SoulBonusPower': u'',
                    'SoulBonusTxt': u'',
                    'abs7Name': u'魅惑の奈落',
                    'abs7Txt': u'超絶大攻撃&自分全回復!!',
                    'angTurnTxt': u'怒ってます！',
                    'artKillName': u'朔望圧縮',
                    'artKillTxt': u'超絶大攻撃&条件達成で即死確率上昇',
                    'bMissTxt': u'おしい…!!失敗した',
                    'bindEndTxt': u'麻痺がとけた!!',
                    'bindTurnTxt': u'麻痺して動くことができない',
                    'bossAttackPattern': u':::,6:4:9:1,1234567890_mag1',
                    'bossDamage_a': u'119941586',
                    'bossHpMax_a': u'75000000',
                    'bossHp_a': u'75000000',
                    'bossTypeNum': u'1',
                    'brr1_5Name': u'金光頑健',
                    'brr1_5Txt': u'ボスの攻撃を3ターン無効化!',
                    'burnEndTxt': u'やけどが治った',
                    'burnTurnTxt': u'やけどのﾀﾞﾒｰｼﾞを受けている',
                    'cMissTxt': u'ﾊｽﾞしてしまった…',
                    'charPassType': u'1',
                    'criG1Name': u'輝く雑草',
                    'criG1Txt': u'超絶攻撃+敵のHPを割合で削る',
                    'darkEndTxt': u'敵を覆う闇が消えた!!',
                    'endTxt': u'戦闘に勝利した!!',
                    'enterBossTxt': u'[情熱]真極･激昂の火焔姫の襲撃！',
                    'fort2TurnTxt': u'姫の怒りがおさまらない!!',
                    'fortTurnTxt': u'激しい焔が敵を襲う!!',
                    'guildHime': u'0',
                    'helpFlg': u'0',
                    'hpEnd': u'100,100,100,100,100,100,100,100,100,100',
                    'hpStart': u'100,100,100,100,100,100,100,100,100,100',
                    'iMissTxt': u'残念…敵のﾔﾙ気を削る事に失敗した!',
                    'immEndTxt': u'敵がﾔﾙ気を取り戻した!気をつけよう!',
                    'immTurnTxt': u'敵は攻撃する気がないようだ!',
                    'killMissTxt': u'即死効果は失敗した!',
                    'limitTurnNum': u'3',
                    'mRnd3Name': u'太陽を追いしもの',
                    'mRnd3Txt': u'敵に5〜8回のﾗﾝﾀﾞﾑ中攻撃!',
                    'mag1NameE': u'悪の波動',
                    'mag1TxtE': u'全体に特大ﾀﾞﾒｰｼﾞ!!',
                    'magBurn5Name': u'放蕩炮烙',
                    'magBurn5Turn': u'3',
                    'magBurn5Txt': u'極大攻撃+確率で3ﾀｰﾝ敵をやけどに!',
                    'magHeal2Name': u'ｳｨｽﾞ･ﾌｧｰｽﾃｨｽ',
                    'magHeal2Txt': u'敵を極大攻撃後、味方全員小回復',
                    'onIcon': u'1,1,1,1,1,1,1,1,1,1',
                    'openingTxt': u'[情熱]真極･激昂の火焔姫の襲撃！',
                    'p10_atLst': u'12038862:abs7::100::1,3439675::::1:,12038862:abs7::100::1',
                    'p10_hp': u'100',
                    'p10_hpLst': u',,100:::',
                    'p1_atLst': u'300575:tornadoImm:a:::1,120230::::1:,300575:tornadoImm::::1',
                    'p1_hp': u'100',
                    'p1_hpLst': u',:::100,100:::',
                    'p2_atLst': u':brr1_5:7:::1,441950::::1:,:brr1_5:4:::1',
                    'p2_hp': u'100',
                    'p2_hpLst': u',,100:::',
                    'p3_atLst': u'693015_7400641:criG1::::1,231005::::1:,693015_330572:criG1::::1',
                    'p3_hp': u'100',
                    'p3_hpLst': u',,100:::',
                    'p4_atLst': u'533900_533900_533900_533900_533900:mRnd3::::1,1334750::::1:,533900_533900_533900_533900_533900_533900_533900:mRnd3::::1',
                    'p4_hp': u'100',
                    'p4_hpLst': u',:100::,100:::',
                    'p5_atLst': u'3338725:magHeal2:5:100::1,1335490::::1:,3338725:magHeal2:4619:100_100_100_100::1',
                    'p5_hp': u'100',
                    'p5_hpLst': u',,100:::',
                    'p6_atLst': u'1813475:magBurn5::::1,725390::::1:,1813475:magBurn5::::1',
                    'p6_hp': u'100',
                    'p6_hpLst': u',100:::,100:::',
                    'p7_atLst': u'1033125:rinp7:a:::1,413250::::1:,1033125:rinp7:a:::1',
                    'p7_hp': u'100',
                    'p7_hpLst': u',,100:::',
                    'p8_atLst': u'20442065_miss:artKill::::1,5840590::::1:,20442065_miss:artKill::::1',
                    'p8_hp': u'100',
                    'p8_hpLst': u',,100:::',
                    'p9_atLst': u'5513182_miss:titaKill2::::1,1575195::::1:,5513182_hit:titaKill2::::1',
                    'p9_hp': u'100',
                    'p9_hpLst': u',::100:,100:::',
                    'playerNum': u'1234567890',
                    'psnEndTxt': u'毒の効果がきれたようだ…!!',
                    'psnTurnTxt': u'毒のﾀﾞﾒｰｼﾞを受けている',
                    'regTurnTxt': u'毎ﾀｰﾝHP回復!',
                    'revMissTxt': u'おしい…!!失敗した',
                    'rinp7Name': u'月と魔術と贖罪と',
                    'rinp7Txt': u'敵全体に攻撃+確率で命中率ﾀﾞｳﾝ!',
                    'skTxt1': u'2,2,幻視の黙示,自分の攻防 極大ｱｯﾌﾟ',
                    'skTxt2': u'1,1236790,[攻撃上昇]ｱﾀﾞﾙﾄ･ﾎﾞﾃﾞｨ,情熱・妖艶ﾀｲﾌﾟの攻撃 極大ｱｯﾌﾟ',
                    'skTxt3': u'12790,12790,[連携]神秘ﾎﾞﾃﾞｨ,妖艶ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt4': u'458,458,[連携]無垢ﾎﾞﾃﾞｨ,清純ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt5': u'670,670,[連携]蠢くﾀﾞｰｸﾈﾋﾞｭﾗ,闇属性の攻防 小ｱｯﾌﾟ',
                    'skillIcon': u'1111111111',
                    'skillNum': u'5',
                    'stlHitTxt': u'強奪に成功した!!',
                    'stlHitTxt_a': u'強奪に成功した!!',
                    'stlHitTxt_b': u'強奪に成功した!!',
                    'stlHitTxt_c': u'強奪に成功した!!',
                    'stlMissTxt': u'無念!強奪に失敗した…',
                    'success': u'1',
                    'timeBonusTxt1': u'',
                    'timeBonusTxt2': u'',
                    'titaKill2Name': u'一緒に踊りましょ♪',
                    'titaKill2Txt': u'敵に超絶大攻撃&確率で即死!',
                    'tokkouBonusColor': u'0,0,0,0,0,0,0,1,1,2,',
                    'tokkouBonusPlayer': u'1,2,3,4,5,6,7,8,9,10,',
                    'tokkouBonusPower': u'2,7,2,7,7,7,7,12,12,20,',
                    'tokkouBonusTxt': u'秘められた力が解放!',
                    'tornadoImmName': u'羽団扇一閃',
                    'tornadoImmTxt': u'極大攻撃+確率で敵が攻撃してこない!',
                    'useBP': u'3',
                    'winHp0': u'0',
                }
            else:
                card1 = get_card(27412213)
                card2 = get_card(26419213)
                card3 = get_card(37406213)
                card4 = get_card(36417213)
                card5 = get_card(16416213)
                card6 = get_card(25378213)
                card7 = get_card(36379213)
                card8 = get_card(34420213)
                card9 = get_card(24421213)
                card10 = get_card(27411213)

                params = {
                    'SoulBonusColor': u'',
                    'SoulBonusPlayer': u'',
                    'SoulBonusPower': u'',
                    'SoulBonusTxt': u'',
                    'abs2Name': u'ﾌﾞﾗｯﾃﾞｨ・ﾚｲﾝ',
                    'abs2Txt': u'敵を攻撃&自分中回復!!',
                    'abs7Name': u'魅惑の奈落',
                    'abs7Txt': u'超絶大攻撃&自分全回復!!',
                    'angTurnTxt': u'怒ってます！',
                    'bMissTxt': u'おしい…!!失敗した',
                    'bindEndTxt': u'麻痺がとけた!!',
                    'bindTurnTxt': u'麻痺して動くことができない',
                    'bossAttackPattern': u':::',
                    'bossDamage_a': u'95510341',
                    'bossHpMax_a': u'75000000',
                    'bossHp_a': u'75000000',
                    'bossTypeNum': u'3',
                    'brr1_5Name': u'金光頑健',
                    'brr1_5Txt': u'ボスの攻撃を3ターン無効化!',
                    'burnEndTxt': u'やけどが治った',
                    'burnTurnTxt': u'やけどのﾀﾞﾒｰｼﾞを受けている',
                    'cMissTxt': u'ﾊｽﾞしてしまった…',
                    'charPassType': u'1',
                    'criG1Name': u'輝く雑草',
                    'criG1Txt': u'超絶攻撃+敵のHPを割合で削る',
                    'darkEndTxt': u'敵を覆う闇が消えた!!',
                    'endTxt': u'戦闘に勝利した!!',
                    'enterBossTxt': u'[清純]真極･激昂の火焔姫の襲撃！',
                    'fort2TurnTxt': u'姫の怒りがおさまらない!!',
                    'fortTurnTxt': u'激しい焔が敵を襲う!!',
                    'guildHime': u'0',
                    'helpFlg': u'0',
                    'hpEnd': u'100,100,100,100,100,100,100,100,100,100',
                    'hpStart': u'100,100,100,100,100,100,100,100,100,100',
                    'iMissTxt': u'残念…敵のﾔﾙ気を削る事に失敗した!',
                    'immEndTxt': u'敵がﾔﾙ気を取り戻した!気をつけよう!',
                    'immTurnTxt': u'敵は攻撃する気がないようだ!',
                    'killMissTxt': u'即死効果は失敗した!',
                    'limitTurnNum': u'1',
                    'mag1NameE': u'悪の波動',
                    'mag1TxtE': u'全体に特大ﾀﾞﾒｰｼﾞ!!',
                    'magBurn5Name': u'放蕩炮烙',
                    'magBurn5Turn': u'3',
                    'magBurn5Txt': u'極大攻撃+確率で3ﾀｰﾝ敵をやけどに!',
                    'magHeal2Name': u'ｳｨｽﾞ･ﾌｧｰｽﾃｨｽ',
                    'magHeal2Txt': u'敵を極大攻撃後、味方全員小回復',
                    'onIcon': u'1,1,1,1,1,1,1,0,0,1',
                    'openingTxt': u'[清純]真極･激昂の火焔姫の襲撃！',
                    'p10_atLst': u'59531937:abs7::100::1',
                    'p10_hpLst': u'',
                    'p1_atLst': u'26620212_miss:titaKill2::::1',
                    'p1_hpLst': u'',
                    'p2_atLst': u':brr1_5:1:::1',
                    'p2_hpLst': u'',
                    'p3_atLst': u'648600_4773118:criG1::::1',
                    'p3_hpLst': u'',
                    'p4_atLst': u'1378012:magHeal2:4:100::1',
                    'p4_hpLst': u'',
                    'p5_atLst': u'516087:magBurn5::::1',
                    'p5_hpLst': u'',
                    'p6_atLst': u'1247425:tornadoImm:a:::1',
                    'p6_hpLst': u'',
                    'p7_atLst': u'102220:abs2::100::1',
                    'p7_hpLst': u'',
                    'p8_atLst': u'164810',
                    'p8_hpLst': u'',
                    'p9_atLst': u'527920',
                    'p9_hpLst': u'',
                    'playerNum': u'1234567890',
                    'psnEndTxt': u'毒の効果がきれたようだ…!!',
                    'psnTurnTxt': u'毒のﾀﾞﾒｰｼﾞを受けている',
                    'regTurnTxt': u'毎ﾀｰﾝHP回復!',
                    'revMissTxt': u'おしい…!!失敗した',
                    'skTxt1': u'1,1234567890,[攻撃上昇]ﾊﾟﾗﾀﾞｲｽ･ﾛｽﾄ,全ﾀｲﾌﾟの攻撃 超絶ｱｯﾌﾟ',
                    'skTxt2': u'3,3478,幻想の終わり終焉の始まり,清純ﾀｲﾌﾟの攻防 超絶ｱｯﾌﾟ',
                    'skTxt3': u'2,2,幻視の黙示,自分の攻防 極大ｱｯﾌﾟ',
                    'skTxt4': u'12690,12690,[連携]神秘ﾎﾞﾃﾞｨ,妖艶ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt5': u'3478,3478,[連携]無垢ﾎﾞﾃﾞｨ,清純ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
                    'skTxt6': u'5790,5790,[連携]蠢くﾀﾞｰｸﾈﾋﾞｭﾗ,闇属性の攻防 小ｱｯﾌﾟ',
                    'skillIcon': u'1111111001',
                    'skillNum': u'6',
                    'stlHitTxt': u'強奪に成功した!!',
                    'stlHitTxt_a': u'強奪に成功した!!',
                    'stlHitTxt_b': u'強奪に成功した!!',
                    'stlHitTxt_c': u'強奪に成功した!!',
                    'stlMissTxt': u'無念!強奪に失敗した…',
                    'success': u'1',
                    'timeBonusTxt1': u'',
                    'timeBonusTxt2': u'',
                    'titaKill2Name': u'一緒に踊りましょ♪',
                    'titaKill2Txt': u'敵に超絶大攻撃&確率で即死!',
                    'tokkouBonusColor': u'1,0,0,0,0,0,0,0,0,2,',
                    'tokkouBonusPlayer': u'1,2,3,4,5,6,7,8,9,10,',
                    'tokkouBonusPower': u'12,7,2,7,7,2,2,3,3,20,',
                    'tokkouBonusTxt': u'秘められた力が解放!',
                    'tornadoImmName': u'羽団扇一閃',
                    'tornadoImmTxt': u'極大攻撃+確率で敵が攻撃してこない!',
                    'useBP': u'3',
                    'winHp0': u'0',
                }

    #skill_text_params = get_special_skill_text_params([])
    #params.update(skill_text_params)

    image_key = 'anim'
    if not request.is_smartphone:
        if get_config(player).get_simple_flash():
            image_key = 'small'
        else:
            image_key = 'medium'
    replace_images = {
        'player_a': boss.card.image_path[image_key],
        'player_b': '',
        'player_c': '',
        'player_1': card1.image_path['small'],
        'player_2': card2.image_path['small'],
        'player_3': card3.image_path['small'],
        'player_4': card4.image_path['small'],
        'player_5': card5.image_path['small'],
        'player_6': card6.image_path['small'],
        'player_7': card7.image_path['small'],
        'player_8': card8.image_path['small'],
        'player_9': card9.image_path['small'],
        'cutin_1': card1.image_path['tall'],
        'cutin_2': card2.image_path['tall'],
        'cutin_3': card3.image_path['tall'],
        'cutin_4': card4.image_path['tall'],
        'cutin_5': card5.image_path['tall'],
        'cutin_6': card6.image_path['tall'],
        'cutin_7': card7.image_path['tall'],
        'cutin_8': card8.image_path['tall'],
        'cutin_9': card9.image_path['tall'],
    }
    if card10:
        replace_images.update({
            'player_10': card10.image_path['small'],
            'cutin_10': card10.image_path['tall'],
        })
    ext = 'gif'
    if request.is_smartphone:
        ext = 'png'
    replace_images['cardBonusImage1'] = u'{}/anims/event/{}/battle/image/battle_point_{}.{}'.format(media_root(), event.resource_path, 3, ext)
    replace_images['cardBonusImage2'] = u'{}/anims/event/{}/battle/image/attack_{}.{}'.format(media_root(), event.resource_path, 3, ext)

    return render_swf_mapping(
        request,
        swf_filename,
        next_url,
        params,
        id_mapper,
        replace_images)


@require_player
def boss_battle_sample_production2(request):
    from module.common.deviceenvironment.device_environment import media_root
    from module.misc.view_utils import render_swf_mapping
    from module.card.api import get_card
    from eventmodule.ecommon.api import get_event

    event = get_event(66)

    if not event:
        return HttpResponseOpensocialRedirect(reverse('fgacha_index'))

    card1 = get_card(17800013)
    card2 = get_card(35838013)
    card3 = get_card(27732013)
    card4 = get_card(37849013)
    card5 = get_card(25727013)
    card6 = get_card(15796013)
    card7 = get_card(35775013)
    card8 = get_card(36802013)
    card9 = get_card(15790013)

    next_url = reverse('limitedgacha_index')
    swf_id_mapper = __import__('{}.swf_id_mapper'.format(event.module), fromlist=['eventmodule'])
    id_mapper = getattr(swf_id_mapper, 'swf_mapping_battle_{}_{}'.format(event.module, 1))
    swf_filename = 'event/{}/battle/raid_battle{}'.format(event.resource_path, 1)

    #skill_text_params = get_special_skill_text_params()
    #params.update(skill_text_params)

    params = {
        'SoulBonusColor': u'',
        'SoulBonusPlayer': u'',
        'SoulBonusPower': u'',
        'SoulBonusTxt': u'',
        'abs1Name': u'あなたの血は何色？',
        'abs1Txt': u'敵を攻撃&自分全回復!!',
        'abs2Name': u'ﾌﾞﾗｯﾃﾞｨ・ﾚｲﾝ',
        'abs2Txt': u'敵を攻撃&自分中回復!!',
        'afterAttackSkill': u'0:0,0:0,0:0,',
        'ang1Name': u'怒り-血湧き肉踊る-',
        'ang1Txt': u'徐々に攻撃UP!!',
        'ang2Name': u'怒髪天昇',
        'ang2Txt': u'徐々に攻撃UP!!',
        'angTurnTxt': u'怒ってます！',
        'b1Txt': u'ﾗｲﾄﾆﾝｸﾞﾎﾞﾙﾄ!1ﾀｰﾝ行動不能!!',
        'bindEndTxt': u'麻痺がとけた!!',
        'bindName': u'ﾗｲﾄﾆﾝｸﾞﾎﾞﾙﾄ',
        'bindTurnTxt': u'麻痺して動くことができない',
        'bindTxt': u'1ﾀｰﾝ行動不能!!',
        'bossAttackPattern': u'13,11,',
        'bossHp': u'800000',
        'bossHpMax': u'800000',
        'c200MissName': u'幸運の一撃',
        'c200MissTxt': u'当たればﾀﾞﾒｰｼﾞ2倍!!',
        'c200Name': u'会心の一撃',
        'c200Txt': u'当たれば2倍!!',
        'c2Txt': u'攻撃力!会心の一撃2倍で攻撃!!',
        'c300Name': u'進撃の一撃',
        'c300Txt': u'当たれば3倍!!',
        'c3Txt': u'攻撃力!進撃の一撃3倍で攻撃!!',
        'cMissTxt': u'ﾊｽﾞしてしまった…',
        'charName': u'全軍への号令',
        'charTxt': u'見よ!姫隊全ての総攻撃!!',
        'cntName': u'殲滅衝動',
        'cntTxt': u'敵の攻撃を避けてｶｳﾝﾀｰ攻撃!',
        'criticalHit2Txt': u'会心の一撃!当たれば2倍!!',
        'criticalHit3Txt': u'進撃の一撃!当たれば3倍!!',
        'doubleStrikeTxt': u'Wｱﾀｯｸ!2回続けて攻撃!!',
        'eName': u'耐久',
        'eTxt': u'HP1で耐えた!!',
        'endTxt': u'戦闘に勝利した!!',
        'enduretxt': u'耐久!hp1で耐えた!!',
        'enterBossTxt': u'[情熱]輝火のﾋﾉｶｸﾞﾂﾁの襲撃！',
        'g10Name': u'天地共鳴',
        'g10Txt': u'敵の残りHPを10%ﾀﾞｳﾝ!!',
        'g3Name': u'ﾒｶﾞｸﾞﾗﾋﾞﾄﾝ',
        'g3Txt': u'敵の残りHPを3%ﾀﾞｳﾝ!!',
        'gravity10Txt': u'ﾎﾞｽの残りHPを10%ﾀﾞｳﾝ!!',
        'guildHime': u'0',
        'heal100Name': u'堕天の歌声',
        'heal100Txt': u'全員のHPを全回復!!',
        'heal100x1Name': u'ﾊｰﾄﾌﾙｽﾏｲﾙ',
        'heal100x1Txt': u'輝く笑顔でHP全回復!',
        'heal25Name': u'天女の羽衣',
        'heal25Txt': u'姫隊全員小回復!!',
        'heal50Name': u'天の加護',
        'heal50Txt': u'姫隊全員中回復!!',
        'healTxt': u'堕天の歌声!全員のHPを全回復!!',
        'judgeTurnNum': u'3',
        'm133Name': u'乱れ撃ち',
        'm133Txt': u'4回連続攻撃!!',
        'm150Name': u'5連みだれ撃ち',
        'm150Txt': u'5回連続攻撃!!',
        'onIcon': u'1,1,1,1,1,1,1,1,1',
        'p1_atLst': u'68765_32450_4613_5755_6290_23018_7476_12380_4275:char:125673849:::1,68765_32450_4613_6334_6290_23018_7476_12380_4275:char:125673849:::1,0',
        'p1_hpLst': u'97_0_0_1_0:97,94_0_0_1_0:91,94_0_0_1_0:91',
        'p2_atLst': u'9735_9735_9735_9735_9735:m150::::1,9735_9735_9735_9735_9735:m150::::1,0',
        'p2_hpLst': u'94_0_0_1_0:94,88_0_0_1_0:81,88_0_0_1_0:81',
        'p3_atLst': u'69134:c300::::1,69134:c300::::1,0',
        'p3_hpLst': u'98:98_0_0_1_0,98:98_0_0_1_0,98:98_0_0_1_0',
        'p4_atLst': u'12380,12380::::1:,0',
        'p4_hpLst': u'99:0_cnt_12380_0_1,99:0_cnt_12380_0_1,99:0_cnt_12380_0_1',
        'p5_atLst': u'80000:g10::::1,36228:g10::::1,0',
        'p5_hpLst': u'94_0_0_1_0:94,88_0_0_1_0:82,88_0_0_1_0:82',
        'p6_atLst': u'6334:ang1::::1,8374:ang1::::1,0',
        'p6_hpLst': u'94_0_0_1_0:94,88_0_0_1_0:82,88_0_0_1_0:82',
        'p7_atLst': u'6290:psn1::::1,6290:psn1::::1,0',
        'p7_hpLst': u'94_0_0_1_0:88,82_0_0_1_0:75,82_0_0_1_0:75',
        'p8_atLst': u'4485_4485:w120::::1,4485_4485:w120::::1,0',
        'p8_hpLst': u'92:92_0_0_1_0,92:92_0_0_1_0,92:92_0_0_1_0',
        'p9_atLst': u'24000:g3::::1,10868:g3::::1,0',
        'p9_hpLst': u'93:93_0_0_1_0,93:93_0_0_1_0,93:93_0_0_1_0',
        'playerNum': u'123456789',
        'psn1Dmg': u'24000',
        'psn1Name': u'即効性ﾎﾟｲｽﾞﾝｼｬﾜｰ',
        'psn1Txt': u'猛毒の雨が降り注ぐ',
        'psn2Name': u'ﾎﾟｲｽﾞﾝﾋﾟﾝｸ',
        'psn2Txt': u'猛毒が敵を襲う!徐々にﾀﾞﾒｰｼﾞ!',
        'psnTurnTxt': u'毒のﾀﾞﾒｰｼﾞを受けている',
        'rev1MissName': u'未熟な反魂の術',
        'rev1MissTxt': u'1/2の確率で姫隊1人蘇生!!',
        'rev1Name': u'黄泉がえりし魂',
        'rev1Txt': u'戦闘不能の姫 復活!!',
        'rev3Name': u'天からの恵み',
        'rev3Txt': u'姫隊3人蘇生!!',
        'revMissTxt': u'おしい…!!失敗した',
        'skTxt1': u'2,2478,[攻撃上昇]神武不殺,清純ﾀｲﾌﾟの攻撃 極大ｱｯﾌﾟ',
        'skTxt2': u'9,169,ｴﾝﾄﾞﾚｽ･ﾌﾚｱ,情熱ﾀｲﾌﾟの攻防 極大ｱｯﾌﾟ',
        'skTxt3': u'8,8,幻視の黙示,自分の攻防 極大ｱｯﾌﾟ',
        'skTxt4': u'2478,2478,[連携]無垢ﾎﾞﾃﾞｨ,清純ﾀｲﾌﾟの攻防 小ｱｯﾌﾟ',
        'skTxt5': u'1289,1289,[連携]煌めくｻﾝﾀﾞｰﾎﾞﾙﾄ,光属性の攻防 小ｱｯﾌﾟ',
        'skTxt6': u'367,367,[連携]蠢くﾀﾞｰｸﾈﾋﾞｭﾗ,闇属性の攻防 小ｱｯﾌﾟ',
        'skillIcon': u'111111111',
        'skillNum': u'6',
        'success': u'1',
        'timeBonusTxt1': u'',
        'timeBonusTxt2': u'',
        'tokkouBonusColor': u'0,0,0,',
        'tokkouBonusPlayer': u'1,2,3,',
        'tokkouBonusPower': u'5,5,2,',
        'tokkouBonusTxt': u'秘められた力が解放!',
        'useBP': u'3',
        'w120Name': u'ﾋﾞｰｽﾄ級Wｱﾀｯｸ',
        'w120Txt': u'2回続けて攻撃!!',
        'w150Name': u'悶絶級Wｱﾀｯｸ',
        'w150Txt': u'50%で続けて攻撃!!',
        'w200Name': u'Wｱﾀｯｸ',
        'w200Txt': u'2回続けて攻撃!!',
        'w2Txt': u'Wｱﾀｯｸ!2回続けて攻撃!!',
        'winHp0': u'1',
    }

    replace_images = {
        'player_1': card1.image_path['small'],
        'player_2': card2.image_path['small'],
        'player_3': card3.image_path['small'],
        'player_4': card4.image_path['small'],
        'player_5': card5.image_path['small'],
        'player_6': card6.image_path['small'],
        'player_7': card7.image_path['small'],
        'player_8': card8.image_path['small'],
        'player_9': card9.image_path['small'],
        'cutin_1': card1.image_path['tall'],
        'cutin_2': card2.image_path['tall'],
        'cutin_3': card3.image_path['tall'],
        'cutin_4': card4.image_path['tall'],
        'cutin_5': card5.image_path['tall'],
        'cutin_6': card6.image_path['tall'],
        'cutin_7': card7.image_path['tall'],
        'cutin_8': card8.image_path['tall'],
        'cutin_9': card9.image_path['tall'],
    }

    ext = 'gif'
    if request.is_smartphone:
        ext = 'png'
    replace_images['cardBonusImage1'] = u'{}/anims/event/{}/battle/image/battle_point_{}.{}'.format(media_root(), event.resource_path, 3, ext)
    replace_images['cardBonusImage2'] = u'{}/anims/event/{}/battle/image/attack_{}.{}'.format(media_root(), event.resource_path, 3, ext)

    return render_swf_mapping(
        request,
        swf_filename,
        next_url,
        params,
        id_mapper,
        replace_images)


@require_player
def notice_simple_flash(request):
    player = request.player

    events = get_enable_events()
    event_banner = ''
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'is_flash_simple': get_config(player).get_simple_flash(),
        'event_banner': event_banner,
        'is_enable_dungeon': Dungeon.get_dungeon_list(),
    })
    page_html = TEMPLATE_PATH + 'battle_mode_change.html'
    return render_to_response(page_html, ctxt)


@require_player
def change_simple_flash_mode(request, on_off, boss_damage_id=None):
    on = str(on_off) == '1'
    get_config(request.player).set_simple_flash(on)
    if boss_damage_id:
        events = get_enable_events()
        if events:
            return HttpResponseOpensocialRedirect(reverse('event{}:event_common_battle_prepare'.format(events[-1].id), args=[boss_damage_id]))
        else:
            return HttpResponseOpensocialRedirect(reverse('help_notice_simple_flash'))
    else:
        return HttpResponseOpensocialRedirect(reverse('help_notice_simple_flash'))


@require_player
def notice_event_voice(request, is_prologue=False):
    player = request.player
    if not request.is_smartphone:
        return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

    events = get_enable_events()
    event_banner = ''
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'is_event_voice': get_config(player).get_event_voice(),
        'event_banner': event_banner,
        'is_prologue': is_prologue,
    })
    page_html = TEMPLATE_PATH + 'event_voice_change.html'
    return render_to_response(page_html, ctxt)


@require_player
def change_event_voice_mode(request, on_off, is_prologue=False):
    on = str(on_off) == '1'
    get_config(request.player).set_event_voice(on)
    if is_prologue:
        return HttpResponseOpensocialRedirect(reverse('help_notice_event_voice_prologue'))
    else:
        return HttpResponseOpensocialRedirect(reverse('help_notice_event_voice'))


@require_player
def next_event_prologue(request):
    events = get_enable_events()
    if events:
        return HttpResponseOpensocialRedirect(reverse('event{}:event_common_quest_story'.format(events[-1].id), args=[1]))
    else:
        return HttpResponseOpensocialRedirect(reverse('help_notice_event_voice'))


@require_player
def application_ban(request):
    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'card1': get_card(26634011),
        'card2': get_card(36633011),
        'card3': get_card(14635011),
        'card4': get_card(34636011),
        'card5': get_card(24637011),
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'application_ban.html'
    return render_to_response(page_html, ctxt)


@require_player
def thanks_money(request):
    player = request.player

    give_coin = None
    if settings.IS_DGAME:
        from module.campaign.special_users import DGAME_SPECIAL_USER_IDS, DGAME_COIN_EXPIRE_DATE, DGAME_GIVE_SPECIAL_COIN
        if DGAME_SPECIAL_USER_IDS.get(player.pk, False):
            campaign_id = DGAME_SPECIAL_USER_IDS.get(player.pk)
            special_campaign_end_at = DGAME_COIN_EXPIRE_DATE.get(campaign_id)
            give_coin = DGAME_GIVE_SPECIAL_COIN.get(player.pk, 0)
        else:
            return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

    else:
        return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    action_record = ActionRecord(request)
    action_record.post_record(player.pk, 'tutorial')

    ctxt = RequestContext(request, {
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
        'special_campaign_end_at': special_campaign_end_at,
        'give_coin': give_coin,
    })
    page_html = TEMPLATE_PATH + 'thanks_money.html'
    return render_to_response(page_html, ctxt)


@require_player
def beginnergacha_help(request):

    events = get_enable_events()
    event_banner = ""
    if events:
        event_banner = get_event_banner(events[-1])

    ctxt = RequestContext(request, {
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'beginnergacha_help.html'
    return render_to_response(page_html, ctxt)


@require_player
def dgame_campaign_help(request):
    '''
    dgame用の使い回し用の施策説明ページ
    '''
    if not settings.IS_DGAME:
        return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

    event = Event(request).get_current_event()
    event_banner = ''
    if event:
        event_banner = get_event_banner(event)

    ctxt = RequestContext(request, {
        'event_banner': event_banner,
        'gashapon_banner': get_active_gashapon_banner(),
    })
    page_html = TEMPLATE_PATH + 'dgame_campaign_help.html'
    return render_to_response(page_html, ctxt)


@require_player
def api_test(request, type=1):
    player = request.player
    type = int(type)

    action_record = ActionRecord(request)

    if type == 1:
        action_record.post_record(player.pk, 'tutorial')
    else:
        action_record.post_record(player.pk, 'invitation')

    return HttpResponseOpensocialRedirect(reverse('thanks_money'))


@require_player
def princess_anim(request, card_id=None):

    choice_card = get_card(card_id)
    print choice_card.id
    choice_cards = [choice_card]

    ctxt_params = {
        'choice_cards': choice_cards,
        'choice_card': choice_card,
    }

    ctxt = RequestContext(request, ctxt_params)
    page_html = TEMPLATE_PATH + 'princess_anim.html'
    return render_to_response(page_html, ctxt)