# -*- coding: utf-8 -*-

import random
import urllib
import datetime

from dateutil.relativedelta import relativedelta

from django.conf import settings
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.http import HttpResponse
from django.contrib.humanize.templatetags.humanize import intcomma

from submodule.horizontalpartitioning import transaction_commit_on_success_hp
from submodule.gsocial.http import HttpResponseOpensocialRedirect
from submodule.gsocial.set_container import containerdata
from submodule.ajax.handler import AjaxHandler
from submodule.gsocial import ActionRecord
from submodule.gamelog.models import DailyAccessLog
from submodule.gsocial.utils.achievement import Achievement

from module.player.api import (get_player_by_osuserid, get_fleshman)
from module.player.decorators import require_player
from module.playercard.battle_api import (
    get_player_attack_front_list,
    get_player_defense_front_list
)
from module.misc.view_utils import render_swf
from module.common.deviceenvironment.device_environment import media_url
from module.common.flash_manager import PromotionFlashManager
from module.playercarddeck.api import get_deck_all
from module.friend.api import get_friend_player_count
from module.serialcampaign.api import get_publish_serialcampaign_list
from module import i18n as T
from module.common.authdevice import is_auth_device_and_just_authorized_now
from module.playerbattleresult.api import get_battle_history_list
from module.bless.api import get_bless_histories
from module.notification.api import get_notification_list
from module.loginbonus.models import LoginStamp
from module.loginbonus.api import get_valid_loginbonus_list, get_extra_or_active_login_stamp
from module.campaign.regist_api import get_active_regist_campaign
from module.campaign.api import get_active_buildup_campaign
from module.playercampaign.api import acquire_regist_campaign
from module.playerloginbonus.api import acquire_login_bonus, acquire_login_stamp, get_latest_login_stamp_history
from module.playerprofile.api import get_profile_comment
from module.playeradventbox.api import get_latest_advent_box_history, acquire_advent_box
from module.playeradventbox.models import PlayerAdventBoxRewardHistory
from module.adventbox.api import get_active_advent_box
from module.bannerarrange.api import get_banner_tag, get_active_arrange_list
from module.bannerarrange.models import ArrangeBase
from module.card.models import DummyCard
from gachamodule.playerfgacha.api import player_one_time_per_day_gashapon
from module.actionlog.api import log_do_growth
from module.information.models import Information as informations
from module.information.models import Information
from module.actionlog.api import log_do_view_page_mypage
from module.battle.api import BATTLE_SIDE_ATTACK, BATTLE_SIDE_DEFENSE, get_battle_member_list
from module.invitation.api import callback_invitation_end_player_tutorial
from module.shop.api import get_limited_shop_list
from module.common import get_cache_limit_of_day
from module.playergashapon.api import player_time_free_gashapon
from module.gashapon.api import get_active_gashapon_stamp
from module.imas_guild.api_pet import get_current_pet
from module.continuancebonus.api import check_continuance_bonus
from module.comebackbonus.api import get_valid_comebackbonus
from module.playercomebackbonus.api import acquire_comebackbonus
from module.continuationcampaign.api import get_valid_continuationcampaign
from module.playercontinuationcampaign.api import check_and_do_continuationcampaign
from module.compensation.api import get_player_compensations
from eventmodule.ecommon.api import get_opening_events, get_ending_events
from eventmodule import Event
from module.navimessage.api import get_navi_message
from eventmodule.ecommon.navi_message import select_navi_message
from module.weekdungeon.models import Dungeon
from module.panelmission.api import mission_clear_flash_cheack
from module.incentive.api import check_incentive_information


def auth_login(request):
    from django.contrib.auth import authenticate, login

    next = 'mobile_root_top'
    message = ''

    if request.method == 'POST':
        if 'username' in request.POST and 'pasword' in request.POST:
            username = request.POST['username']
            password = request.POST['pasword']
            if 'next' in request.POST:
                next = request.POST['next']

            if not next:
                next = 'mobile_root_top'
            user = authenticate(username=username, password=password)
            if user is not None:
                if user.is_active:
                    login(request, user)
                    return HttpResponseOpensocialRedirect(reverse(next))
        message = u'認証できませんでした'
    else:
        if 'next' in request.GET:
            next = request.GET['next']
    ctxt = RequestContext(request, {
        'message': message,
        'next': next,
    })
    return render_to_response('root/auth/login.html', ctxt)


def auth_logout(request):
    from django.contrib.auth import logout
    logout(request)
    return HttpResponseOpensocialRedirect(reverse('auth_login'))


def _log_daily_access(_debug=False):
    from functools import wraps
    from django.db import connection, transaction

    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwds):
            #if not settings.IS_COLOPL:
            osuser_id = request.player.pk
            now = datetime.datetime.now()
            is_smartphone = getattr(request, 'is_smartphone', False)
            selectsql = 'SELECT EXISTS (SELECT 1 FROM gamelog_dailyaccesslog WHERE osuser_id=%s AND DATE(accessed_at) = DATE(%s))'
            selectparam = [osuser_id, now.strftime("%Y-%m-%d")]
            cursor = connection.cursor()
            cursor.execute(selectsql, selectparam)
            for row in cursor.fetchone():
                if row == 0:
                    sql = 'INSERT INTO gamelog_dailyaccesslog(osuser_id,accessed_at,is_smartphone) VALUES(%s,%s,%s)'
                    param = [osuser_id,now.strftime("%Y-%m-%d %H:%M:%S"),is_smartphone]
                    cursor.execute(sql, param)
                    transaction.commit_unless_managed()
            return view_func(request, *args, **kwds)
        return _wrapped_view
    return decorator


@require_player
@_log_daily_access()
def root_top(request):

    player = get_player_by_osuserid(request.osuser.userid)
    if player is None:
        return HttpResponseOpensocialRedirect(reverse('prologue_index'))

    # Ameba 事前登録API
    if settings.IS_AMEBA or settings.IS_MOBCAST:
        check_incentive_information(request, player.pk)

    if settings.IS_COLOPL and not player.consent.is_agree(1):
        return HttpResponseOpensocialRedirect(reverse('consent_colopl'))

    player = request.player
    if not player.is_end_tutorial():
        return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

    ##==最新3件のお知らせを表示
    #notification_pager, notification_list = get_notification_list(limit=3, sort=u'published_at', reverse=True)
    notification_list = list()
    notification_lists = list()
    if request.is_smartphone:
        notification_pager, notification_list = get_notification_list(category=1, limit=3, sort=u'published_at', reverse=True)
        notification_pager, notification_lists = get_notification_list(category=3, limit=3, sort=u'published_at', reverse=True)
    else:
        notification_pager, notification_list = get_notification_list(limit=3, sort=u'published_at', reverse=True)

    fleshman_list = get_fleshman(player.pk, 1)

    if len(fleshman_list) < 1:
        fleshman = None
    else:
        fleshman = fleshman_list[0]

    banners = get_banner_tag(ArrangeBase.TOPPAGE)
    #==有効なシリアルキャンペーンを表示

    serialcampaign_list = get_publish_serialcampaign_list()
    serialcampaign_list.reverse()

    gashapon_stamp = get_active_gashapon_stamp()
    from module.seek.api import HIDDEN_TYPE_APP_TOP, is_not_found
    is_seek_event = is_not_found(player, HIDDEN_TYPE_APP_TOP)
    ctxt = RequestContext(request, {
        'notification_list': notification_list,
        'notification_lists': notification_lists,
        'target_player': fleshman,
        'banners': banners,
        'serialcampaign_list': serialcampaign_list,
        'gashapon_stamp': gashapon_stamp,
        'is_seek_event': is_seek_event,
        'type': player.encryption(HIDDEN_TYPE_APP_TOP),
    })

    return render_to_response('root/top.html', ctxt)


#==リストの表示件数
def _history_list_select(history, num):
    history_list = []
    for i, hist in enumerate(history):
        if i > num - 1:
            break
        history_list.append(hist)

    return history_list


@require_player
@_log_daily_access()
@transaction_commit_on_success_hp
def root_index(request):
    player = request.player

    log_do_view_page_mypage()

    if settings.IS_COLOPL and not player.consent.is_agree(1):
        return HttpResponseOpensocialRedirect(reverse('consent_colopl'))

    if player.growth == 0:
        Information.reset_growth(player.pk)


    # 浮いたセッション情報を消す
    try:
        request.session.pop("add_card_ids", None)
        request.session.pop("buildup_add_id", None)
        request.session.pop("buildup_result", None)
        request.session.pop("checked_card_ids", None)
        request.session.pop("buildup_is_include_rare", None)
        request.session.pop("battle_ready_url", None)
        request.session.pop("GROWTH_RETURN_URL", None)
        request.session.pop("doli_raid2_result", None)  # 一時対応
        request.session.pop("tower_result", None)  # 一時対応
    except:
        pass  # セッション情報の削除に失敗してもガタガタ言わない


    # 端末認証をチェックする -- 内部でキャッシュされている(gsocial)
    if not player.flag_is_done_invite_callback():
        isu_auth_device, is_auth_now = is_auth_device_and_just_authorized_now(request)

        # たった今端末認証ができたので特典を付与する
        if is_auth_now:
            callback_invitation_end_player_tutorial(player)
            player.flag_on_done_invite_callback()
            player.save()

        # 認証済み状態で後からライフサイクルイベントが来た場合、ここで報酬配布
        if isu_auth_device and player.flag_is_need_invite_callback():
            callback_invitation_end_player_tutorial(player)
            player.flag_off_need_invite_callback()
            player.flag_on_done_invite_callback()
            player.save()


    # コラボCP用ログインカウンタ
    from module.papp.game.api.collabo_app.models import PlayerHistory
    from module.papp.game.api.collabo_app.api import get_active_collabo
    collabo = get_active_collabo()
    if collabo:
        PlayerHistory.increment_login_count(player.pk, request.osuser.age, collabo.pk, request.is_smartphone)

    animation = _root_index_animation(request, player)
    if animation:
        return animation

    # 最終ログイン日時を記録
    player.set_last_login_at()


    Event.induction(player)
    Event.rare_boss_introduction(player)
    Event.guerrilla_boss_introduction(player)

    friend_count = get_friend_player_count(player)

    #==戦闘履歴
    battle_history_list = get_battle_history_list(player, limit=2)

    #==挨拶履歴
    bless_history_list = get_bless_histories(player.pk, request, limit=2)

    my_guild = player.guild

    #==最新3件のお知らせを表示
    notification_list = list()
    notification_lists = list()
    if request.is_smartphone:
        notification_pager, notification_list = get_notification_list(category=1, limit=3, sort=u'published_at', reverse=True)
        notification_pager, notification_lists = get_notification_list(category=3, limit=3, sort=u'published_at', reverse=True)
    else:
        notification_pager, notification_list = get_notification_list(limit=3, sort=u'published_at', reverse=True)
    # 未読の最新お知らせがある場合は、新着にのせる。
    news_id = 0
    before_news_id = player.get_latest_news()
    try:
        news_id = notification_list[0].id
    except IndexError:
        news_id = 0

    if not before_news_id:
        before_news_id = news_id
        player.set_latest_news(news_id)

    if before_news_id < news_id:
        Information.set_notification(player.pk)
        player.set_latest_news(news_id)

    #補償ｱｲﾃﾑがあるか
    if not informations._get_compensation(player.pk):
        get_player_compensations(player)

    information = informations.get_messages(player.pk, request.is_smartphone)
    for msg in Event(request).information():
        information.append({'name': msg.title, 'url': msg.url})

    # 自己紹介文章
    mycomment = get_profile_comment(player)

    banner_list = get_active_arrange_list()
    banners_top = get_banner_tag(ArrangeBase.MYPAGE_TOP, banner_list)
    banners_mid = get_banner_tag(ArrangeBase.MYPAGE_MIDDLE, banner_list)
    banners_btm = get_banner_tag(ArrangeBase.MYPAGE_BOTTOM, banner_list)
    banners_slide = get_banner_tag(ArrangeBase.MYPAGE_SLIDE, banner_list)

    ''' マイベッドのカード選出 '''
    show_order = (1, 2, 3, 4, 5)

    if not request.is_smartphone:
        show_order = (4, 2, 1, 3, 5)

    deck_list = get_deck_all(player)
    player_cards = player.cards_cache()
    mapper = {
        1: get_player_attack_front_list,
        2: get_player_defense_front_list,
    }

    leadercard = player.leader_player_card()

    # 表示させるカードはコスト関係無いからコスト999固定値
    # マイベットなので5人固定なのです
    #show_card_list, _, _, _ = mapper[random.choice([1, 2])](player, 999, 5, player_cards)
    #show_card_list = [x[1] for x in show_card_list]
    
    show_card_list = []
    show_card_list.append(leadercard)
    
    # 表示するカードから、コメントを表示するカードを選出
    comment_index = random.randint(1, len(show_card_list))

    greet_card = show_card_list[comment_index - 1]
    comment_index = show_order.index(comment_index) + 1

    if not request.is_smartphone:
        show_card_list += [DummyCard() for i in range(5 - len(show_card_list))]  # カードが5枚以下の場合、ダミー画像を差し込む
        show_card_list = [show_card_list[i - 1] for i in show_order]  # カードを並び替える

    # 自己紹介URL
    if settings.IS_COLOPL:
        myprofile_tag = containerdata['app_url'] % {"app_id": settings.APP_ID, "userid": player.pk}
    elif settings.IS_AMEBA:
        profile_url = "http://" + settings.SITE_DOMAIN + reverse("profile_show", args=[player.pk])
        myprofile_tag_sp = '<a href="{}">ﾏｲﾍﾞｯﾄﾞ</a>'.format(profile_url)
        myprofile_tag = myprofile_tag_sp
    else:
        profile_url = urllib.quote("http://" + settings.SITE_DOMAIN + reverse("profile_show", args=[player.pk]), "~")
        fp_url = containerdata['app_url'] % {"app_id": settings.APP_ID}
        fp_url += '?guid=ON&url=' + profile_url
        if settings.IS_GREE:
            if settings.OPENSOCIAL_SANDBOX:
                platform_domain = 'pf-sb.gree.net/{}'.format(settings.APP_ID)
            else:
                platform_domain = 'pf.gree.net/{}'.format(settings.APP_ID)
            profile_url_sp = urllib.quote("http://" + settings.SITE_DOMAIN_SP + reverse("profile_show", args=[player.pk]), "~")
            sp_url = "http://" + platform_domain
            sp_url += "?url=" + profile_url_sp
        else:
            sp_url = containerdata['app_url_sp'] % {"app_id": settings.APP_ID}
            sp_url += "?url=" + profile_url
        if settings.IS_DGAME:
            if settings.OPENSOCIAL_SANDBOX:
                query = '?apid=%s&url=' % settings.APP_ID
                sp_url = sp_url.replace('?url=', query)
                fp_query = '?apid=%s&guid=ON&url=' % settings.APP_ID
                fp_url = fp_url.replace('?guid=ON&url=', fp_query)

            myprofile_tag_fp = '<dcon title="ﾏｲﾍﾞｯﾄﾞ(ｹｰﾀｲはこちら)" href="{}"/>'.format(fp_url)
            myprofile_tag_sp = '<dcon title="ﾏｲﾍﾞｯﾄﾞ(ｽﾏｰﾄﾌｫﾝはこちら)" href="{}"/>'.format(sp_url)
        else:
            myprofile_tag_fp = '<a href="{}">ﾏｲﾍﾞｯﾄﾞ(ｹｰﾀｲはこちら)</a>'.format(fp_url)
            myprofile_tag_sp = '<a href="{}">ﾏｲﾍﾞｯﾄﾞ(ｽﾏｰﾄﾌｫﾝはこちら)</a>'.format(sp_url)
        myprofile_tag = myprofile_tag_sp + myprofile_tag_fp

    #デッキの攻撃力、防御力
    #(ここの処理は非常に重い。スマホでしか使用していないので、ガラケーでは計算しない。)
    if request.is_smartphone:
        front, back, _, _ = get_battle_member_list(player, BATTLE_SIDE_ATTACK, is_max=True, player_cards=player_cards, deck_list=deck_list)
        attack_battle_power = sum([pc.attack() for pc in (front + back)])
        front, back, _, _ = get_battle_member_list(player, BATTLE_SIDE_DEFENSE, is_max=True, player_cards=player_cards, deck_list=deck_list)
        defense_battle_power = sum([pc.defense() for pc in (front + back)])
    else:
        # ガラケーのHTML側では利用していないはずだが、念のためダミーを定義
        attack_battle_power = 1000
        defense_battle_power = 1000

    event_callback = Event(request)

    event = event_callback.get_current_event()
    event_callback.update_rescue_info()
    info_msg = event_callback.get_group_match_info(player)
    if info_msg == player:
        # 返り値が同じならNoneに
        info_msg = None

    navi_message = get_navi_message(player, request.is_smartphone)
    event_boss_info = event_callback.get_event_boss_info()
    is_rescue = None
    if event_boss_info:
        is_rescue = event_boss_info.get('is_rescue', None)
    event_navi_message = select_navi_message(player, event, is_rescue, info_msg)

    limited_shop_list = get_limited_shop_list()
    limited_shop = None
    if limited_shop_list:
        limited_shop = limited_shop_list[0]

    campaign = get_active_buildup_campaign(player)

    is_bookmark_close = player.get_bookmark_close

    ad_params = {}
    if settings.IS_GREE:
        ad_params = _get_advertise_params(request)

    archive_bonus_init_kvs = player.get_kvs('archive_bonus')
    if not archive_bonus_init_kvs.get(False):
        from module.playercard.api import init_archive_or_love_max_bonus
        init_archive_or_love_max_bonus(player)
        archive_bonus_init_kvs.set(True)

    if not event:
        events = get_opening_events()
        if events:
            event = events[0]
    if event:
        event_index_viewname = 'event{}:event_common_index'.format(event.id)
    else:
        event_index_viewname = 'event_common_index'

    # ameba用のドットマネー対応
    dotmoney_stat = {}
    if settings.IS_AMEBA:
        if not settings.OPENSOCIAL_DEBUG:
            achievement = Achievement(request)
            dotmoney_stat = achievement.get_stat(player.pk)
            item_box_count_stat = achievement.get_item_box_count(player.pk)
            today = datetime.date.today()
            expiration_date = datetime.date(today.year, today.month, 1) + relativedelta(months=1) - datetime.timedelta(days=1)
            dotmoney_left_day = expiration_date - today
            if item_box_count_stat and 'item_box_count' in item_box_count_stat and item_box_count_stat['item_box_count'] > 0:
                information.append({'name': u'ドットマネーの交換アイテムが届いています!', 'url': reverse('gift_index')})
            if dotmoney_stat:
                if 'amebapoint_center_text' in dotmoney_stat and 'amebapoint_top_url' in dotmoney_stat:
                    information.append({'name': u'【アメーバからのお知らせ】{}'.format(dotmoney_stat['amebapoint_center_text']), 'url': dotmoney_stat['amebapoint_top_url']})
                if dotmoney_left_day.days <= 7 and 'expiration_point' in dotmoney_stat:
                    if dotmoney_left_day.days >= 2:
                        dot_info_msg = u'あと{}日で'.format(dotmoney_left_day.days)
                    else:
                        dot_info_msg = u'本日'
                    dot_info_msg = u'{}あなたのドットマネー {}マネーが失効します'.format(dot_info_msg, intcomma(int(dotmoney_stat['expiration_point'])))

                    information.append({'name': u'【アメーバからのお知らせ】{}'.format(dot_info_msg), 'url': '#'})

    # mobcast用のペロ対応
    pero_stat = {}
    if settings.IS_MOBCAST:
        if not settings.OPENSOCIAL_DEBUG:
            achievement = Achievement(request)
            pero_stat = achievement.get_stat(player.pk)


    if greet_card:
        if greet_card.rarity >= 19:
            mybed_card_voice = greet_card.detail.voice_url_by_id(2)
        else:
            mybed_card_voice = greet_card.detail.voice_url_by_id(random.choice(range(1, 15)))

    ctxt = RequestContext(request, {
        'player_card_front_list': show_card_list,
        'friend_count': friend_count,
        'battle_history_list': battle_history_list,
        'bless_history_list': bless_history_list,
        'notification_list': notification_list,
        'notification_lists': notification_lists,
        'banners_top': banners_top,
        'banners_mid': banners_mid,
        'banners_btm': banners_btm,
        'banners_slide': banners_slide,
        'mycomment': mycomment,
        'information': information,
        'greet_card': greet_card,
        'idx': comment_index,
        'my_guild': my_guild,
        'attack_battle_power': attack_battle_power,
        'defense_battle_power': defense_battle_power,
        'myprofile_tag': myprofile_tag,
        'campaign': campaign,
        'event': event,
        'event_index_viewname': event_index_viewname,
        'limited_shop': limited_shop,
        'guild_pet': get_current_pet(),
        'is_bookmark_close': is_bookmark_close,
        'ad_params': ad_params,
        'navi_message': navi_message,
        'event_navi_message': event_navi_message,
        'group_match_info': info_msg,
        'event_boss_info': event_boss_info,
        'enable_dungeon': Dungeon.get_dungeon_list(),
        'dotmoney_stat': dotmoney_stat,
        'pero_stat': pero_stat,
        'mybed_card_voice': mybed_card_voice,
    })

    response = render_to_response('root/index.html', ctxt)
    return response


@require_player
def mood_callback(request):
    player = request.player
    #cache = _get_mood_send_limit(player)
    #if cache.get() == 0:
    kvs = player.get_kvs('fgacha_302')
    if not kvs.get():
        from module.gift.api import npc_give_gift
        npc_give_gift(player.pk, settings.ENTITY_TYPE_ITEM, 206, 1, u'{}送信による報酬です｡'.format(T.SNS_SAY))
        #cache.set(1)
        kvs.set(True)
    return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))


def _get_mood_send_limit(player):
    return get_cache_limit_of_day("gashapon_sendmood1224:" + player.pk, 0)


def ad_program(player):
    """
    GREE広告３種の「成果タグ」
    """
    import hashlib
    ad_program_key = None
    if player:
        temp = hashlib.md5('%s%s' % (player.pk, T.AD_PROGRAM_KEY)).hexdigest()
        ad_program_key = '%s_%s' % (player.pk, temp)

    return ad_program_key


def _generate_growth_list(growth):
    '''
    良い感じのステップの配列をつくる
    '''
    result = []
    for v in range(growth + 1):
        if v <= 0:
            continue
        if v <= 10:
            result.append(v)
        elif v % 5 == 0:
            result.append(v)
    if growth > 10 and growth % 5 != 0:
        result.append(growth)
    return result


@require_player
def root_growth_index(request):
    player = request.player
    growth = player.growth
    ## growthをパースする
    growth_list = _generate_growth_list(growth)

    event = Event(request).get_current_event()
    event_banner = u''
    if event:
        event_banner = Event(request).get_encount_banner_callback() or u''

    ctxt = RequestContext(request, {
        'growth_list': growth_list,
        'event_banner': event_banner,
    })
    return render_to_response('root/growth.html', ctxt)


@require_player
def root_end_event_list(request):
    ctxt = RequestContext(request, {
        'end_event_list': get_ending_events(),
    })
    return render_to_response('root/end_event_list.html', ctxt)

@require_player
def root_zoning_index(request):
    ctxt = RequestContext(request, {})
    return render_to_response('root/zoning.html', ctxt)

@require_player
def root_growth_execution(request, category=0):
    player = request.player
    category = category
    number = request.POST.get('growth_val', 0)

    category = int(category)
    number = int(number)
    log_do_growth(player, number, category)
    growth_map = {
        1: lambda number: player.growth_vitality(number),
        2: lambda number: player.growth_attack(number),
        3: lambda number: player.growth_defense(number),
    }
    growth_map[category](number)
    player.save(force_update=True)
    if player.growth == 0:
        Information.reset_growth(player.pk)
    return HttpResponseOpensocialRedirect(reverse('root_growth_result', args=[category, number]))


@require_player
def root_growth_result(request, category, number):
    player = request.player
    growth = player.growth
    if not growth:
        # 無い場合は呼び出し元に戻る
        return_url = request.session.get('GROWTH_RETURN_URL')
        if return_url:
            request.session['GROWTH_RETURN_URL'] = None
            return HttpResponseOpensocialRedirect(return_url)
    ## growthをパースする
    growth_list = _generate_growth_list(growth)

    event = Event(request).get_current_event()
    event_banner = u''
    if event:
        event_banner = Event(request).get_encount_banner_callback() or u''

    ctxt = RequestContext(request, {
        'category': int(category),
        'number': number,
        'growth_list': growth_list,
        'event_banner': event_banner,
    })
    return render_to_response('root/growth.html', ctxt)


@require_player
def root_cooperate(request):

    ctxt = RequestContext(request, {
    })
    return render_to_response('root/cooperate.html', ctxt)


@require_player
def root_fleshman_list(request):
    player = request.player
    player_list = get_fleshman(player.pk, 10)

    ctxt = RequestContext(request, {
        'player_list': player_list,
    })
    return render_to_response('root/fleshman_list.html', ctxt)


def _root_index_animation(request, player):

    flash_manager = PromotionFlashManager(player)

    # 登録キャンペーン
    regist_campaign = get_active_regist_campaign(player)
    if regist_campaign and flash_manager.can_show_movie():
        flag = acquire_regist_campaign(player, regist_campaign)
        if flag:
            return HttpResponseOpensocialRedirect(reverse('regist_campaign_production', args=[regist_campaign.pk]))

    # カムバックキャンペーン
    if player.get_last_login_at():
        comebackbonus = get_valid_comebackbonus()
        if comebackbonus:
            acquire_comebackbonus_id = acquire_comebackbonus(request, comebackbonus)
            if acquire_comebackbonus_id:
                if comebackbonus.flag_is_continuous_campaign():
                    return HttpResponseOpensocialRedirect(reverse('comeback_login_production'))
                return HttpResponseOpensocialRedirect(reverse('comebackbonus_index', args=[]), request)


    advent_box = get_active_advent_box()
    if advent_box and flash_manager.can_show_movie():
        advent_box_history = getattr(request, 'login_bonus_history', None) or get_latest_advent_box_history(player)
        advent_box, position = acquire_advent_box(player, advent_box_history)
        if advent_box and position:
            flash_manager.count_up()
            return HttpResponseOpensocialRedirect(reverse('advent_box_production', args=[advent_box.pk]))

    login_stamp = get_extra_or_active_login_stamp(player)
    if login_stamp and flash_manager.can_show_movie():
        login_stamp_history = getattr(request, 'login_bonus_history', None)
        if login_stamp_history is None or isinstance(login_stamp_history, PlayerAdventBoxRewardHistory):
            login_stamp_history = get_latest_login_stamp_history(player, login_stamp)
        try:
            login_stamp, position, step, step_count = acquire_login_stamp(player, login_stamp_history, login_stamp)
        except LoginStamp.ContinuationException:
            return HttpResponseOpensocialRedirect(reverse('mobile_root_index'))

        if login_stamp:
            flash_manager.count_up()
            return HttpResponseOpensocialRedirect(reverse('login_stamp_production', args=[login_stamp.pk, position, step, step_count]))

    # 継続ボーナス
    if check_continuance_bonus(player) and flash_manager.can_show_movie():
        flash_manager.count_up()
        return HttpResponseOpensocialRedirect(reverse('continuance_bonus_production', args=[]))

    # ログインボーナス
    if flash_manager.can_show_movie():
        login_bonus_list = get_valid_loginbonus_list()
        login_bonus_list = acquire_login_bonus(player, login_bonus_list, request)
        if login_bonus_list:
            flash_manager.count_up()
            return HttpResponseOpensocialRedirect(reverse('login_bonus_production', args=[login_bonus_list[0].group]))

    if flash_manager.can_show_movie() and mission_clear_flash_cheack(player.pk):
        flash_manager.count_up()
        return HttpResponseOpensocialRedirect(reverse('panelmission_mission_clear_execution'))

    # リワードキャンペーン
    continuationcampaign_list = get_valid_continuationcampaign()
    continuationcampaign = [r for r in continuationcampaign_list if r.trigger_id == 1]
    if continuationcampaign:
        if flash_manager.can_show_movie() and check_and_do_continuationcampaign(player, continuationcampaign[0]):
            flash_manager.count_up()
            return HttpResponseOpensocialRedirect(reverse('continuationcampaign_production', args=[]))

    # 無料ガチャ系
    time_free_gashapon = player_time_free_gashapon(request)
    free_gashapons = [player_one_time_per_day_gashapon(player), time_free_gashapon]
    is_gashapon_enable = False
    for gashapon in free_gashapons:
        if gashapon and gashapon.is_enable():
            Information.set_normal_gacha(player.pk)
            is_gashapon_enable = True
            break
    if not is_gashapon_enable:
        Information.reset_normal_gacha(player.pk)

    return None


def auth_device_error(request):
    '''
    非対応端末エラー
    '''
    ctxt = RequestContext(request, {})
    response = render_to_response('root/auth_device_error.html', ctxt)
    response.delete_cookie('scid')
    return response


def root_auth(request):
    """
    iOS6対応コード
    """
    import time
    now = time.time()
    callback_url = '/m/' if settings.OPENSOCIAL_DEBUG else containerdata['app_url_sp'] % {"app_id": settings.APP_ID}
    res = HttpResponseRedirect(callback_url)
    res.set_cookie("created_at", now, max_age=2592000, path='/')

    return res


def grant_strage_access(request):
    """
    mixi対応
    """
    callback_url = '/m/' if settings.OPENSOCIAL_DEBUG else containerdata['app_url_sp'] % {"app_id": settings.APP_ID}
    ctxt = RequestContext(request, {
        'callback_url': callback_url,
    })
    return render_to_response('root/grant_strage_access.html', ctxt)

@require_player
def bookmark_close(request):
    request.player.set_bookmark_close()
    ajax = AjaxHandler(request)
    ajax.set_ajax_param('text', "OK")
    ctxt_params = {}
    #ctxt = RequestContext(request, ctxt_params)
    return HttpResponse(ajax.get_ajax_param(ctxt_params), mimetype='text/json')


@require_player
def root_anim_invitation_introduce(request):
    return render_swf(request, 'root/invitation_introduce', reverse("invitation_index"), {})


def _get_advertise_params(request):
    # とりあえず対応だよ
    # 3日連続ログインしたユーザーはタグを表示する
    import hashlib
    player = request.player
    sha256_osuser_id = hashlib.sha256(player.pk).hexdigest()
    key = settings.GREEAD_LOGIN_ADVERTISEMENT + u':' + settings.GREEAD_LOGIN_CAMPAIGN_ID + u':' + str(sha256_osuser_id) + u':' + settings.GREEAD_LOGIN_SITE_KEY
    digest = hashlib.sha256(key).hexdigest()

    is_staging = settings.OPENSOCIAL_SANDBOX
    is_product = not is_staging and not settings.DEBUG

    kvs = player.get_kvs('gree_ad_login_campaign')

    if not kvs.get() and player.regist_past_day == settings.GREEAD_LOGIN_COUNT:
        login_count = DailyAccessLog.objects.using("read").filter(osuser_id=player.pk).count()
        if login_count >= settings.GREEAD_LOGIN_COUNT:
            params = {
                # 'ad_program_md5_key': ad_program(request.opensocial_viewer_id),
                "sha256_osuser_id": sha256_osuser_id,
                "digest": digest,
                "is_product": is_product,
            }
            kvs.set(True)
        else:
            params = {}
    else:
        params = {}

    return params


def _logging_special_users(player_id, str):
    '''
    特定のユーザーIDのみログ吐くよ(GREEのみ) 
    # あほか終わったら消せよ2017/04/27 by kyou
    '''
    if not settings.IS_GREE:
        return
    import logging

    SPECIAL_USER_IDS = [
        u'17023',
        u'16928030',
        u'6704082',
        u'16163103',
    ]

    if player_id in SPECIAL_USER_IDS:
        logging.error('[SPECIAL {}] {}'.format(player_id, str))


@require_player
def dgame_api_test(request):
    action_record = ActionRecord(request)
    action_record.post_record(request.player.pk, 'login3days')
    return HttpResponseOpensocialRedirect(reverse('mobile_root_top'))

@require_player
def xr_anim(request, page):
    player = request.player
    ctxt = RequestContext(request, {
        'page_id': page,
    })
    
    return render_to_response('card/miyabiEffect/' + page + '/main.html', ctxt)