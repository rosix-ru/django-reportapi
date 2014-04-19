/* reportapi.js for ReportAPI
 * 
 * Copyright 2014 Grigoriy Kramarenko.
 * 
 * This file is part of ReportAPI.
 * 
 * ReportAPI is free software: you can redistribute it and/or modify
 * it under the terms of the GNU General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 * 
 * ReportAPI is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU General Public License for more details.
 * 
 * You should have received a copy of the GNU General Public License
 * along with ReportAPI.  If not, see <http://www.gnu.org/licenses/>.
 * 
 * Этот файл — часть ReportAPI.
 * 
 * ReportAPI - свободная программа: вы можете перераспространять ее и/или
 * изменять ее на условиях Стандартной общественной лицензии GNU в том виде,
 * в каком она была опубликована Фондом свободного программного обеспечения;
 * либо версии 3 лицензии, либо (по вашему выбору) любой более поздней
 * версии.
 * 
 * ReportAPI распространяется в надежде, что она будет полезной,
 * но БЕЗО ВСЯКИХ ГАРАНТИЙ; даже без неявной гарантии ТОВАРНОГО ВИДА
 * или ПРИГОДНОСТИ ДЛЯ ОПРЕДЕЛЕННЫХ ЦЕЛЕЙ. Подробнее см. в Стандартной
 * общественной лицензии GNU.
 *
 * Вы должны были получить копию Стандартной общественной лицензии GNU
 * вместе с этой программой. Если это не так, см.
 * <http://www.gnu.org/licenses/>.
 * 
 */

////////////////////////////////////////////////////////////////////////
//                   КОНСТАНТЫ И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ                //
////////////////////////////////////////////////////////////////////////
var TIMEOUT_PROGRESS = 1000,
    SERVER_TZ_OFFSET = window.SERVER_TZ_OFFSET || -240; // Europe/Moscow

// Глобальные хранилища-регистраторы
window.TEMPLATES = {}; // Шаблоны

////////////////////////////////////////////////////////////////////////
//                            НАСТРОЙКИ                               //
////////////////////////////////////////////////////////////////////////

/* Настройки шаблонизатора underscore.js в стиле Django */
//~ _.templateSettings = {
    //~ interpolate: /\{\{(.+?)\}\}/g,
    //~ evaluate: /\{\%(.+?)\%\}/g, 
//~ };

/* Включение Underscore.string методов в пространство имён Underscore */
_.mixin(_.str.exports());

////////////////////////////////////////////////////////////////////////
//                               ОБЩИЕ                                //
////////////////////////////////////////////////////////////////////////

/* Единая, переопределяемая задержка для действий или функций */
delay = (function(){
    var timer = 0;
    return function(callback, ms){
        if (DEBUG) {console.log('function:'+'delay '+ms)};
        clearTimeout (timer);
        timer = setTimeout(callback, ms);
    };
})();

/* Общие функции вывода сообщений */
function handlerHideAlert() {
    if (DEBUG) {console.log('function:'+'handlerHideAlert')};
    $('.alert').alert('close');
    $('#alert-place').css('z-index', '-1000');
};
function handlerShowAlert(msg, type, callback, timeout) {
    if (DEBUG) {console.log('function:'+'handlerShowAlert')};
    timeout = timeout || 5000;
    console.log(msg);
    if (!type) { type = 'alert-danger'; };
    html = TEMPLATES.alert({ msg: msg, type: type });
    $('#alert-place').css('z-index', '1000').html(html);
    $(window).scrollTop(0);
    $('.alert').alert();
    if (callback) { delay(callback, timeout); }
    else { delay(handlerHideAlert, timeout); };
    return false;
};

/* Общая функция для работы с django-quickapi */
function jsonAPI(args, callback, to_console, sync, timeout) {
    if (DEBUG) {console.log('function:'+'jsonAPI')};
    if (!args) { args = { method: "reportapi.get_scheme" } };
    if (!callback) { callback = function(json, status, xhr) {} };
    var jqxhr = $.ajax({
        type: "POST",
        async: !sync,
        timeout: timeout || AJAX_TIMEOUT,
        url: REPORTAPI_API_URL,
        data: {'jsonData': $.toJSON(args), 'language': window.LANGUAGE_CODE},
        dataType: 'json'
    })
    // Обработка ошибок протокола HTTP
    .fail(function(xhr, status, err) {
        // Если есть переадресация, то выполняем её
        if (xhr.getResponseHeader('Location')) {
            location = xhr.getResponseHeader('Location')
            .replace(/\?.*$/, "?next=" + window.location.pathname);
            window.location.replace(location);
            console.log("1:" + xhr.getResponseHeader('Location'));
        } else {
            // Иначе извещаем пользователя ответом и в консоль
            console.log("ERROR:" + xhr.responseText);
            if (xhr.responseText) {
                handlerShowAlert(_(xhr.responseText).truncate(255), 'alert-danger');
            };
        };
    })
    // Обработка полученных данных
    .done(function(json, status, xhr) {
        if (to_console) { if (DEBUG) {console.log(to_console)}; };
        /* При переадресации нужно отобразить сообщение на некоторое время,
         * а затем выполнить переход по ссылке, добавив GET-параметр для
         * возврата на текущую страницу
         */
        if ((json.status >=300) && (json.status <400) && (json.data.Location != undefined)) {
            redirect = function() {
                location = json.data.Location
                .replace(/\?.*$/, "?next=" + window.location.pathname);
                window.location.replace(location);
            }
            if (json.message) {
                handlerShowAlert(json.message, 'alert-danger', redirect);
            }
            else { redirect() }
        }
        /* При ошибках извещаем пользователя полученным сообщением */
        else if (json.status >=400) {
            handlerShowAlert(json.message, 'alert-danger');
        }
        /* При нормальном возврате в debug-режиме выводим в консоль
         * сообщение
         */
        else {
            if (DEBUG) {
                o = new Object;
                $.extend(true, o, json.data);
                //~ console.log(o);
                console.log($.toJSON(json.message));
            };
            return callback(json, status, xhr);
        };
    });
    return jqxhr
};

////////////////////////////////////////////////////////////////////////
//                          Обработчики отчётов                       //
////////////////////////////////////////////////////////////////////////

/* Обработчик создания отчёта */
function handlerCreateReport(force) {
    if (DEBUG) {console.log('function:'+'handlerCreateReport')};
    $('.action-preview, .action-remove, .action-download')
        .attr('disabled', 'disabled');
    window.REPORT.id = null;
    window.REPORT.process_filters = {};
    $.each(window.REPORT.filters, function(key, item) {
        if (item.condition || item.value != null) {
            window.REPORT.process_filters[item.name] = {condition:item.condition, value:item.value};
        };
    });
    args = {
        'method': 'reportapi.document_create',
        'section': window.REPORT.section,
        'name': window.REPORT.name,
        'filters': window.REPORT.process_filters,
        'force': force,
    };
    cb = function(json, status, xhr) {
        
    };

    var jqxhr = jsonAPI(args, cb, null, false, window.REPORT.timeout);
    handlerStartProgress();
    return jqxhr;
};

/* Обработчик события создания отчёта */
function eventCreateReport(event) {
    if (DEBUG) {console.log('function:'+'eventCreateReport')};
    handlerCreateReport();
};

/* Обработчик события пересоздания отчёта */
function eventRecreateReport(event) {
    if (DEBUG) {console.log('function:'+'eventRecreateReport')};
    handlerCreateReport(true);
};

/* Обработчик запуска ожидания создания отчёта */
function handlerCheckProcess() {
    if (DEBUG) {console.log('function:'+'handlerCheckProcess')};
    args = {
        'method': 'reportapi.document_info',
        'id': window.REPORT.id || null,
        'section': window.REPORT.section,
        'name': window.REPORT.name,
        'filters': window.REPORT.process_filters,
    };

    cb = function(json, status, xhr) {
        $obj = $('.progress .progress-bar');
        max = Number($obj.attr('aria-valuemax'));
        now = Number($obj.attr('aria-valuetransitiongoal'));
        window.REPORT.id = json.data.id;
        window.REPORT.timeout = json.data.timeout;
        if (json.data.end) {
            clearInterval(window.REPORT.process);
            window.REPORT.process = undefined;
            $obj.attr('aria-valuetransitiongoal', max).progressbar();
            
            url = json.data.url + window.REPORT.format.toLowerCase() + '/';

            $('.action-preview')
                .attr('onClick', "handlerShowDocument('"+json.data.url+"', 'document-"+json.data.id+"')")
                .removeAttr('disabled').show();
            if (json.data.error) {
                $('.action-download').attr('disabled', 'disabled').hide();
                $('.action-remove')
                    .attr('onClick', "handlerRemoveDocument("+json.data.id+")")
                    .attr('disabled', 'disabled').show();
                if (json.data.has_remove) {
                    $('.action-remove').removeAttr('disabled');
                };
                $('.action-preview')
                    .removeClass('btn-default').addClass('btn-warning')
                    .find('.fa').removeClass('fa-search').addClass('fa-bug');
            } else {
                $('.action-remove').attr('disabled', 'disabled').hide();
                $('.action-download')
                    .attr('href', url)
                    .removeAttr('disabled').show();
                $('.action-preview')
                    .removeClass('btn-warning').addClass('btn-default')
                    .find('.fa').removeClass('fa-bug').addClass('fa-search');
            };
            $('.progress')
                .removeClass('progress-striped')
                .removeClass('active')
                .hide();
            $obj.attr('aria-valuetransitiongoal', 0).progressbar();

            if (window.REPORT.create_force) {
                $('.action-create-report:visible').hide();
                $('.action-recreate-report:hidden').show();
            } else {
                $('.action-create-report').prop("disabled", true);
            };
            //~ $('.progress').hide(500);
        } else if (now >= max){
            //~ $obj.attr('aria-valuetransitiongoal', (max/100)*99).progressbar();
            $('.progress')
                .addClass('progress-striped')
                .addClass('active');
        } else {
            $obj.attr('aria-valuetransitiongoal', TIMEOUT_PROGRESS + now).progressbar();
        };
    };

    var jqxhr = jsonAPI(args, cb);
    return jqxhr;
};

/* Обработчик запуска ожидания создания отчёта */
function handlerStartProgress() {
    if (DEBUG) {console.log('function:'+'handlerStartProgress')};
    $('.action-create-report').prop("disabled", true);
    $('.progress .progress-bar')
        .attr('aria-valuemax', window.REPORT.timeout || TIMEOUT_PROGRESS)
        .attr('aria-valuetransitiongoal', 1)
        .progressbar();
    $('.progress').show();
    
    window.REPORT.process = setInterval(function () {
        handlerCheckProcess();
    }, window.TIMEOUT_PROGRESS);
};

/* Обработчик удаления отчёта */
function handlerRemoveDocument(id) {
    if (DEBUG) {console.log('function:'+'handlerRemoveDocument')};
    if (id) {
        var args = {
                'method': 'reportapi.document_delete',
                'id': id,
            },
            success = function() {
                $('.action-preview, .action-remove, .action-download')
                    .attr('disabled', 'disabled').hide();
                $('#thumbnail-document-'+id).remove();
            };
        new jsonAPI(args, success);
    };
    
};

/* Обработчик события удаления отчёта */
function eventRemoveDocument(event) {
    if (DEBUG) {console.log('function:'+'eventRemoveDocument')};
    var id = null;
    handlerRemoveDocument(id);
};

////////////////////////////////////////////////////////////////////////
//                    Обработчики типов фильтров                      //
////////////////////////////////////////////////////////////////////////

/* Обработчик установки поиска-выбора для фильтров объектов */
function handlerSetSelectizers($box) {
    if (DEBUG) {console.log('function:'+'handlerSetSelectizers')};
    $box = $box || $('body');

    $.each($box.find('select[data-type="object"]'), function(index, select) {

        if (select.name) {
            var filter = window.REPORT.filters[select.name],
                unicode_key = filter.unicode_key || '__unicode__';
            $(select).selectize({
                valueField: 'pk',
                labelField: unicode_key,
                searchField: filter.fields_search || unicode_key,
                create: false,
                options: filter.options,
                maxItems: (filter.condition == 'range') ? 2 : undefined,
                render: {
                    option: function(item, escape) {
                        return  '<div>' +
                                    '<span class="pull-right"> #' + escape(item.pk) + '</span>' +
                                    '<span>' + escape(item[unicode_key]) + '</span>' +
                                '</div>';
                    }
                },
                load: function(query, callback) {
                    if (!query.length) return callback();
                    if (filter.search_on_date) {
                        var day = moment(query);
                        if (day.invalidAt() > -1 || query.length <10) {
                            return callback();
                        };
                    };

                    var args = {
                            'method': "reportapi.object_search",
                            'section': window.REPORT.section || null,
                            'name': window.REPORT.name,
                            'filter_name': filter_name,
                            'query': query,
                        },
                        success = function(res) {
                            //~ console.log(res);
                            callback(res.data.object_list);
                        };
                    new jsonAPI(args, success);
                },
                onChange: function(value) {
                    if (filter.condition == 'range' && value.length != 2) {
                        filter.value = null;
                    } else {
                        filter.value = (value == '') ? null : value;
                    };
                    handlerAfterChanges();
                },
                onClear: function() {
                    filter.value = null;
                    handlerAfterChanges();
                }
            });
        }
    });

    other = $box.find('select[data-type="choice"], select[data-type="month"], select[data-type="weekday"]');
    $.each(other, function(index, select) {

        if (select.name) {
            var filter = window.REPORT.filters[select.name];
            $(select).selectize({
                options: filter.options,
                valueField: 'value',
                labelField: 'label',
                searchField: 'label',
                create: false,
                maxItems: (filter.condition == 'range') ? 2 : undefined,
                onChange: function(value) {
                    if (filter.condition == 'range' && value.length != 2) {
                        filter.value = null;
                    } else {
                        filter.value = (value == '') ? null : value;
                    };
                    handlerAfterChanges();
                },
                onClear: function() {
                    filter.value = null;
                    handlerAfterChanges();
                }
            });
        }
    });
};

/* Обработчик установки масок для input */
function handlerMaskInputs($box) {
    if (DEBUG) {console.log('function:'+'handlerMaskInputs')};
    $box = $box || $('body');

    // Инициализация маски для дат
    $.mask.definitions['1']='[0-1]';
    $.mask.definitions['2']='[0-2]';
    $.mask.definitions['3']='[0-3]';
    $.mask.definitions['5']='[0-5]';
    $.each($box.find('[data-mask]'), function(i, item) {
        $item = $(item);
        data = $(item).data();
        $item.mask(data.mask, {
            completed: function() {
                filter = REPORT.filters[this.context.name];
                filter.value = this.val();
                if (filter.condition == 'range') {
                    filter.value = filter.value.split(RANGE_SPLIT);
                };
            }
        });
    });

    return true;
};

/* Обработчик проверки обязательных фильтров */
function handlerCheckRequiredValue() {
    if (DEBUG) {console.log('function:'+'handlerCheckRequiredValue')};//, event)};

    completed = true;
    $.each(REPORT.filters, function(key, item) {
        if ((item.required) && (item.value === null || item.value === undefined)) {
            completed = false;
        };
    });
    if (completed) {
        $('.action-create-report').prop("disabled", false);
    } else {
        $('.action-create-report').prop("disabled", true);
    };
    return completed;
};

/* Постобработчик изменения значения или условия фильтра */
function handlerAfterChanges() {
    if (DEBUG) {console.log('function:'+'handlerAfterChanges')};
    if (window.REPORT.process) {
        clearInterval(window.REPORT.process);
        window.REPORT.id = null;
        window.REPORT.process = null;
    };
    $('.progress:visible').hide();
    $('.progress .progress-bar').attr('aria-valuetransitiongoal', 0)
        .progressbar();
    $('.action-preview:visible').hide();
    $('.action-download:visible').hide();
    $('.action-recreate-report:visible').hide();
    $('.action-create-report:hidden').show();
    $('.action-preview, .action-remove, .action-download')
        .attr('disabled', 'disabled').hide();
    handlerCheckRequiredValue();
};

// События


/* Обработчик события изменения значения фильтра */
function eventChangeValue(event) {
    if (DEBUG) {console.log('function:'+'eventChangeValue')};//, event)};
    value = $(event.target).val();
    filter = REPORT.filters[event.target.name];
    if (event.target.type == 'checkbox') {
        filter.value = event.target.checked;
    } else if ($(event.target).attr('data-mask') !== undefined) {
        filter.value = value ? filter.value : null;
    } else {
        filter.value = value || null;
    };
    handlerAfterChanges();
};

/* Обработчик события изменения условия фильтра */
function eventConditionChange(event) {
    if (DEBUG) {console.log('function:'+'eventConditionChange')};//, event)};

    filter_name = $(event.target).data()['name'];
    filter = REPORT.filters[filter_name];
    filter.condition = event.target.value || null;
    //~ console.log(filter.condition);
    if (filter.condition in {'isnull':0, 'empty':0}) {
        filter.value = false;
    } else if (!filter.condition || filter.condition in {'range':0,'in':0} || filter.type == 'object') {
        filter.value = null;
    } else {
        filter.value = $('#value-'+filter_name).val() || null;
    };
    html = TEMPLATES.filter({ data: filter });
    $('#valuebox-'+filter_name).html(html);
    handlerSetSelectizers($('#valuebox-'+filter_name));
    handlerMaskInputs($('#valuebox-'+filter_name));

    handlerAfterChanges();

    return true;
};


/* Проверка события нажатия клавиши управления браузером */
function keyDownIsControl(event) {
    if (DEBUG) {console.log('function:'+'keyDownIsControl')};//, event)};
    if ((event.which == 8) // backspace
        || (event.which == 9) // tab
        || (event.which == 13) // enter
        || (event.which == 27) // escape
        || (event.which >= 33 && event.which <= 46) // Page Up - Delete
        || (event.which >= 112 && event.which <= 145) // F1 - ScrollLock
    ) { return true }
    return false;
};

/* Обработчик события нажатия клавиши на поле ввода дат и времени */
function eventKeyDownOnDateTime(event) {
    if (DEBUG) {console.log('function:'+'eventKeyDownOnDateTime')};//, event)};

    prepare = function(event) {
        value = event.target.value || '';
        //~ console.log(value, event.charCode);
    };

    // Enabled keys browser control
    if (keyDownIsControl(event)) { return true }
    // Replace valide values
    else if (event.which >= 48 && event.which <= 57) { // 0-9
        prepare(event);
        return true;
    }

    return false;
};


/* Обработчик события нажатия клавиши на поле ввода чисел */
function eventKeyDownOnNumber(event) {
    //~ if (DEBUG) {console.log('function:'+'eventKeyDownOnNumber')};//, event)};

    adddot = function(event) {
        value = event.target.value || '';
        //~ console.log('search', value.search('.'));
        if (value.length < 1) {
            event.target.value = '0.';
        }
        else if (value.indexOf('.') < 0) {
            event.target.value = event.target.value + '.';
        }
    };

    // Enabled keys
    if ((event.which >= 48 && event.which <= 57) // 0-9
        || keyDownIsControl(event) // browser control
    ) { return true }
    // Replace decimal point
    else if (event.which == 188 || event.which == 190) {
        adddot(event);
        return false;
    }

    return false;
};

////////////////////////////////////////////////////////////////////////
//                              ПРОЧЕЕ                                //
////////////////////////////////////////////////////////////////////////

/* Обработчик просмотра отчёта */
function handlerShowDocument(href, name) {
    if (DEBUG) {console.log('function:'+'handlerShowDocument')};
    var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
    win.focus();
};

/* Обработчик отображения дополнительных фильтров */
function handlerShowAdditionalFilters() {
    if (DEBUG) {console.log('function:'+'handlerShowAdditionalFilters')};
    $('.additional-filter').show();
    $('button.action-hide-additional').show();
    $('button.action-show-additional').hide();

    return true;
};

/* Обработчик сокрытия дополнительных фильтров */
function handlerHideAdditionalFilters() {
    if (DEBUG) {console.log('function:'+'handlerHideAdditionalFilters')};
    $('.additional-filter').hide();
    $('button.action-hide-additional').hide();
    $('button.action-show-additional').show();
    return true;
};


/* Обработчик установки шаблонов */
function handlerTemplates() {
    if (DEBUG) {console.log('function:'+'handlerTemplates')};

    TEMPLATES.alert  = _.template($('#underscore-alert').html());
    TEMPLATES.filter = _.template($('#underscore-filter').html());

    return true;
};

/* Обработчик установки биндингов для элементов */
function handlerBindinds() {
    if (DEBUG) {console.log('function:'+'handlerBindinds')};

    // Биндинг на сокрытие алерта
    $('body').on('click', 'button.close[data-dismiss="alert"]', 
        function () {$('#alert-place').css('z-index', '-1000');});

    $('body').on('change', 'select[id^="condition-"]', eventConditionChange);
    $('body').on('keydown', 'input[data-validate="number"]', eventKeyDownOnNumber);
    $('body').on('change', 'input[id^="value-"]', eventChangeValue);
    $('body').on('click', '.action-hide-additional', handlerHideAdditionalFilters);
    $('body').on('click', '.action-show-additional', handlerShowAdditionalFilters);
    $('body').on('click', '.action-create-report', eventCreateReport);
    $('body').on('click', '.action-recreate-report', eventRecreateReport);

    // Биндинги на отчёты
    //~ $('body').on('click', '[data-action=object_print]',   eventObjectPrint);
    //~ $('body').on('click', '[data-action=object_print]',   eventObjectPrint);

    return true;
};

////////////////////////////////////////////////////////////////////////
//                            ИСПОЛНЕНИЕ                              //
////////////////////////////////////////////////////////////////////////

/* Выполнение чего-либо после загрузки страницы */
$(document).ready(function($) {
    if (DEBUG) {console.log('function:'+'$(document).ready')};

    // Инициализация шаблонов Underscore
    handlerTemplates();

    // Инициализация для Bootstrap и плагинов
    $("alert").alert();
    $(".dropdown-toggle").dropdown();

    // Установка биндингов для элементов
    handlerBindinds();

    // Прочее
    handlerMaskInputs();
    handlerHideAdditionalFilters();

});
