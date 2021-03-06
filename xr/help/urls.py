# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns, url

urlpatterns = patterns(
    'help.views',
    url(r'^$', 'help_index', name='help_index'),
    url(r'^detail/(?P<help_id>\d+)/$', 'help_detail', name='help_detail'),
    url(r'^chain_skill/$', 'help_chain_skill', name='help_chain_skill'),
    url(r'^item/ice/$', 'help_item_ice', name='help_item_ice'),
    url(r'^rainbow/slime/$', 'help_rainbow_slime', name='help_rainbow_slime'),
    url(r'^event_rainbow/slime/$', 'help_event_rainbow_slime', name='help_event_rainbow_slime'),
    url(r'^skill/slime/$', 'help_skill_slime', name='help_skill_slime'),
    url(r'^new/princess/(?:(?P<select_new_card_id>\w+)/)?$', 'new_princess', name='new_princess'),
    url(r'^special/material/card/list/(?:(?P<card_id>\d+)/)?$', 'help_special_material_card_list', name='help_special_material_card_list'),
    url(r'^mini_fairy/$', 'help_mini_fairy', name='help_mini_fairy'),
    url(r'^axis_3/$', 'axis_3', name='axis_3'),
    url(r'^skill/limited/$', 'limited_skill_description', name='limited_skill_description'),
    url(r'^rarity/new_princess/$', 'rarity_new_princess', name='rarity_new_princess'),
    url(r'^soul/soul_seed_pr/$', 'soul_seed_pr', name='soul_seed_pr'),
    url(r'^card/card_explanation/$', 'card_explanation', name='card_explanation'),
    url(r'^buildup/skill_up/$', 'skill_level_up', name='skill_level_up'),
    url(r'^card/introduction/$', 'card_introduction', name='card_introduction'),
    url(r'^notice/event_guild/$', 'notice_event_guild', name='notice_event_guild'),
    url(r'^mood_callback/$', 'mood_callback', name='help_mood_callback'),
    url(r'^special_skill/explanation/page/(?:(?P<page>\d+)/)?$', 'special_skill_explanation', name='special_skill_explanation_page'),
    url(r'^special_skill/explanation/(?:(?P<skill_id>\d+)/)?$', 'special_skill_explanation', name='special_skill_explanation'),
    url(r'^special_skill/explanation/$', 'special_skill_explanation', name='special_skill_explanation'),
    url(r'^function_will/(?:(?P<page>\d+)/)?$', 'function_will', name='function_will'),
    url(r'^million_notice/$', 'million_notice', name='million_notice'),
    url(r'^boss/battle/sample/production/$', 'boss_battle_sample_production', name='boss_battle_sample_production'),
    url(r'^boss/battle/sample/production2/$', 'boss_battle_sample_production2', name='boss_battle_sample_production2'),
    url(r'^notice/simple_flash/$', 'notice_simple_flash', name='help_notice_simple_flash'),
    url(r'^change/simple_flash/(?P<on_off>[01])/$', 'change_simple_flash_mode', name='help_change_simple_flash_mode'),
    url(r'^change/simple_flash/(?P<on_off>[01])/(?P<boss_damage_id>\d+)/$', 'change_simple_flash_mode', name='help_change_simple_flash_mode'),
    url(r'^config/event_voice/$', 'notice_event_voice', name='help_notice_event_voice'),
    url(r'^config/event_voice/prologue/$', 'notice_event_voice', kwargs={'is_prologue':True}, name='help_notice_event_voice_prologue'),
    url(r'^config/event_voice/(?P<on_off>[01])/$', 'change_event_voice_mode', name='help_change_event_voice_mode'),
    url(r'^config/event_voice/(?P<on_off>[01])/prologue/$', 'change_event_voice_mode', kwargs={'is_prologue':True}, name='help_change_event_voice_mode_prologue'),
    url(r'^config/event_voice/next_prologue/$', 'next_event_prologue', name='help_next_event_prologue'),
    url(r'^application_ban/$', 'application_ban', name='application_ban'),
    url(r'^thanks_money/$', 'thanks_money', name='thanks_money'),
    url(r'^dgame_campaign_help/$', 'dgame_campaign_help', name='dgame_campaign_help'),
    url(r'^beginnergacha_help/$', 'beginnergacha_help', name='beginnergacha_help'),
    url(r'^api_test/(?P<type>\d+)/$', 'api_test', name='help_api_test'),
    url(r'^aprilfool_campaign/$', 'aprilfool_campaign', name='aprilfool_campaign'),
    url(r'^campaign/3th/$', 'campaign_3th', name='campaign_3th'),
    url(r'^princess_anim/(?P<card_id>\d+)/$', 'princess_anim', name='princess_anim'),
)
