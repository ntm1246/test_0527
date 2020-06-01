# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

# root
urlpatterns = patterns(
    'root.views',
    url(r'^top/$', 'root_top', name='mobile_root_top'),
    url(r'^$', 'root_index', name='mobile_root_index'),
    url(r'^mybed/$', 'root_index', name='mobile_root_index_mixi'),
#    url(r'^authlogin/$', 'auth_login', name='auth_login'),
#    url(r'^auth/logout/$', 'auth_logout', name='auth_logout'),

    # あいさつ
    #url(r'^greet/exection/(?P<target_player_id>\w+)/$', 'root_greet_execution', name='mobile_root_greet_execution'),

    url(r'^growth/$', 'root_growth_index', name='root_growth_index'),
    url(r'^growth/(?P<category>\w+)/$', 'root_growth_execution', name='mobile_root_growth_execution'),
    url(r'^growth/(?P<category>\w+)/(?P<number>\w+)/$', 'root_growth_result', name='root_growth_result'),

    url(r'^fleshman/list/$', 'root_fleshman_list', name='root_fleshman_list'),

    url(r'^end_event_list/$', 'root_end_event_list', name='root_end_event_list'),
    url(r'^anim_invitation_introduce/$', 'root_anim_invitation_introduce', name='root_anim_invitation_introduce'),

    # Greeゾーニング対応
    url(r'^zoning/$', 'root_zoning_index', name='root_zoning_index'),

    #非対応端末エラー
    url(r'^auth/device/error/$', 'auth_device_error', name='auth_device_error'),

    url(r'^cooperate/$', 'root_cooperate', name='mobile_root_cooperate'),
    url(r'^auth/$', 'root_auth', name='root_auth'),
    url(r'^grant/$', 'grant_strage_access', name='grant_strage_access'),

    #SPのブックマーク推奨のアレを一生消す
    url(r'^bookmark_close/$', 'bookmark_close', name='bookmark_close'),

    #ひとこと
    url(r'^mood_callback/$', 'mood_callback', name='root_mood_callback'),

    # Dgame api test
    url(r'^api_test/$', 'dgame_api_test', name='dgame_api_test'),

    # XR対応
    url(r'^xr_anim/(?P<page>\d+)/$', 'xr_anim', name='xr_anim'),
)

urlpatterns += patterns(
    'root.animations',
    url(r'^time/free/gashapon/(?P<timeslot>\d+)/$', 'root_time_free_gashapon', name='mobile_root_time_free_gashapon'),
)
