(function () {
    'use strict';

    var website = openerp.website;
    website.add_template_file('/website_gengo/static/src/xml/website.gengo.xml');

    website.EditorBar.include({
        events: _.extend({}, website.EditorBar.prototype.events, {
            'click a[data-action=translation_gengo]': 'translation_gengo',
            'click a[data-action=translation_gengo_post]': 'translation_gengo_post',
            'click a[data-action=translation_gengo_info]': 'translation_gengo_info',
            'click a[data-action=reload]': 'reload',
        }),
        start: function () {
            this.gengo_translate = false;
            this._super.apply(this, arguments);
            var self = this;
            var gengo_langs = ["ar_SA","id_ID","nl_NL","fr_CA","pl_PL","zh_TW","sv_SE","ko_KR","pt_PT","en_US","ja_JP","es_ES","zh_CN","de_DE","fr_FR","fr_BE","ru_RU","it_IT","pt_BR"];
            if (gengo_langs.indexOf(website.get_context()['lang']) != -1)
                {
                self.$('button[data-action=edit]')
                    .after(openerp.qweb.render('website.ButtonGengoTranslator'));
                
                }
        },
        translation_gengo: function () {
            var self = this;
            if(!localStorage['website_gengo_nodialog']){
                var dialog = new website.GengoTranslatorDialog();
                dialog.appendTo($(document.body));
                self.gengo_translate = true;
                dialog.on('activate', this, function () {
                    localStorage['website_gengo_nodialog'] = dialog.$('input[name=do_not_show]').prop('checked') || '';
                    dialog.$el.modal('hide');
                    self.translation_gengo_display()
                });
            }
            else{
                self.gengo_translate = true;
                self.translation_gengo_display()
            }
        },
        translation_gengo_display:function(){
            var self = this;
            self.translate().then(function () {
                self.gengo_translate = false;
                if($('.oe_translatable_todo').length > 0){
                    self.$el.find('form.navbar-form.navbar-left > *').addClass("hidden");
                    self.$el.find('.gengo_post,.gengo_info,.gengo_discard').removeClass("hidden");
                }
                else{
                    self.$el.find('form.navbar-form.navbar-left > *').addClass("hidden");
                    self.$el.find('.gengo_inprogress,.gengo_info,.gengo_discard').removeClass("hidden");
                }
            });
        },
        translation_gengo_post: function () {
            var self = this;
            var translatable_list = $.find('.oe_translatable_todo');
            var dialog = new website.GengoTranslatorPostDialog();
            dialog.appendTo($(document.body));
            dialog.on('service_level', this, function () {
                var gengo_service_level = dialog.$el.find(".form-control").val();
                dialog.$el.modal('hide');
                self.$el.find('.gengo_post,.gengo_discard').addClass("hidden");
                self.$el.find('.gengo_wait').removeClass("hidden");
                var trans ={}
                $('.oe_translatable_todo').each(function () {
                    var $node = $(this);
                    var data = $node.data();
                    if (!trans[data.oeTranslationViewId]) {
                        trans[data.oeTranslationViewId] = [];
                    }
                    trans[data.oeTranslationViewId].push({
                        initial_content: self.getInitialContent(this),
                        new_content:self.getInitialContent(this),
                        translation_id: data.oeTranslationId || null,
                        gengo_translation: gengo_service_level
                    });
                });
                openerp.jsonRpc('/website/set_translations', 'call', {
                    'data': trans,
                    'lang': website.get_context()['lang'],
                }).then(function () {
                    $('.oe_translatable_todo').addClass('oe_translatable_inprogress').removeClass('oe_translatable_todo');
                    self.$el.find('.gengo_wait').addClass("hidden");
                    self.$el.find('.gengo_inprogress,.gengo_discard').removeClass("hidden");
                }).fail(function () {
                    alert("Could not Post translation");
                });
            });
            
        },
        translation_gengo_info: function () {
            var repr =  $(document.documentElement).data('mainObject')
            var view_id = repr.match(/.+\((.+), (\d+)\)/)[2];
            openerp.jsonRpc('/website/get_gengo_info', 'call', {
                'view_id': view_id,
                'lang': website.get_context()['lang'],
            }).done(function(res){
                var dialog = new website.GengoTranslatorStatisticDialog(res);
                dialog.appendTo($(document.body));
                
            });
        },
        reload: function () {
            website.reload();
        },
    });
    
    website.GengoTranslatorDialog = openerp.Widget.extend({
        events: _.extend({}, website.EditorBar.prototype.events, {
            'hidden.bs.modal': 'destroy',
            'click button[data-action=activate]': function (ev) {
                this.trigger('activate');
            },
        }),
        template: 'website.GengoTranslatorDialog',
        start: function () {
            this.$el.modal();
        },
    });
    
    website.GengoTranslatorPostDialog = openerp.Widget.extend({
        events: _.extend({}, website.EditorBar.prototype.events, {
            'hidden.bs.modal': 'destroy',
            'click button[data-action=service_level]': function (ev) {
                this.trigger('service_level');
            },
        }),
        template: 'website.GengoTranslatorPostDialog',
        start: function () {
            this.$el.modal();
        },
    });
    
    website.GengoTranslatorStatisticDialog = openerp.Widget.extend({
        events: _.extend({}, website.EditorBar.prototype.events, {
            'hidden.bs.modal': 'destroy',
        }),
        template: 'website.GengoTranslatorStatisticDialog',
        init:function(res){
            var self = this;
            this.total =  res.total;
            this.inprogess =  res.inprogess;
            this.done =  res.done;
            this.new_words =  0;
            $('.oe_translatable_todo').each(function () {
                self.new_words += $(this).text().trim().replace(/ +/g," ").split(" ").length;
            });
            return this._super.apply(this, arguments);
        },
        start: function (res) {
            this.$el.modal(this.res);
        },
    });

})();
