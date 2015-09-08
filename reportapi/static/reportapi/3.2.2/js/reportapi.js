/* reportapi.js for ReportAPI
 * 
 * Repository: https://bitbucket.org/rosix/django-reportapi
 * 
 * Copyright 2014-2015 Grigoriy Kramarenko <root@rosix.ru>
 *
 * This file is part of ReportAPI.
 *
 * ReportAPI is free software: you can redistribute it and/or
 * modify it under the terms of the GNU Affero General Public License
 * as published by the Free Software Foundation, either version 3 of
 * the License, or (at your option) any later version.
 *
 * ReportAPI is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public
 * License along with ReportAPI. If not, see
 * <http://www.gnu.org/licenses/>.
 * 
 */

////////////////////////////////////////////////////////////////////////
//                   КОНСТАНТЫ И ГЛОБАЛЬНЫЕ ПЕРЕМЕННЫЕ                //
////////////////////////////////////////////////////////////////////////
window.TEMPLATES = {}; // Скомпилированные шаблоны underscore

////////////////////////////////////////////////////////////////////////
//                               ОБЩИЕ                                //
////////////////////////////////////////////////////////////////////////

/* Единая, переопределяемая задержка для действий или функций */
delay = (function(){
    var timer = 0;
    return function(callback, ms){
        clearTimeout (timer);
        timer = setTimeout(callback, ms);
    };
})();

/* Общие функции вывода сообщений */
function handlerHideAlert() {
    $('.alert').alert('close');
    $('#alert-place').css('z-index', '-1000');
};

function handlerShowAlert(msg, type, callback, timeout) {
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
        var o, redirect;

        if (to_console) { console.log(to_console) };

        /* При переадресации нужно отобразить сообщение на некоторое время,
         * а затем выполнить переход по ссылке, добавив GET-параметр для
         * возврата на текущую страницу
         */
        if ((json.status >=300) && (json.status <400) && (json.data.Location != undefined)) {
            redirect = function() {
                var location = json.data.Location
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
            clearInterval(window.REPORT.process);
            window.REPORT.process = undefined;
            $('.progress .progress-bar').removeClass('progress-bar-striped active');
            handlerSetProgress(0);
        }
        /* При нормальном возврате в debug-режиме выводим в консоль
         * сообщение
         */
        else {
            if (DEBUG) {
                o = new Object;
                $.extend(true, o, json.data);
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
    $('.action-create-report, .action-recreate-report, .action-preview, .action-download, .action-remove')
        .attr('disabled', 'disabled');
    $('#view-document-place').hide();

    window.REPORT.id = null;
    window.REPORT.process_filters = {};
    $.each(window.REPORT.filters, function(key, item) {
        if (item.value != null && item.value != undefined) {
            window.REPORT.process_filters[item.name] = {
                condition: item.condition,
                value: (item.server_value != undefined) ? item.server_value : item.value,
            };
        };
    });
    var args = {
        'method': 'reportapi.document_create',
        'section': window.REPORT.section,
        'name': window.REPORT.name,
        'filters': window.REPORT.process_filters,
        'force': force},
        cb = function(json, status, xhr) {};

    var jqxhr = jsonAPI(args, cb, null, false, window.REPORT.timeout);
    handlerStartProgress();
    return jqxhr;
};

/* Обработчик запуска ожидания создания отчёта */
function handlerCheckProcess() {
    var args = {
        'method': 'reportapi.document_info',
        'id': window.REPORT.id || null,
        'section': window.REPORT.section,
        'name': window.REPORT.name,
        'filters': window.REPORT.process_filters,
    };

    var cb = function(json, status, xhr) {
        var $pbar = $('.progress .progress-bar'),
            max = Number($pbar.attr('aria-valuemax')),
            now = Number($pbar.attr('aria-valuenow'));
        window.REPORT.id = json.data.id;
        window.REPORT.timeout = json.data.timeout;
        if (json.data.end) {
            // report ready
            clearInterval(window.REPORT.process);
            window.REPORT.process = undefined;
            handlerSetProgress(max);

            if (json.data.error) {
                $('.action-preview')
                    .attr('onclick', "handlerShowDocument('"+json.data.urls.view.auto+"', 'document-"+json.data.id+"')")
                    .prop("disabled", false)
                    .removeAttr('disabled')
                    .removeClass('btn-default btn-success')
                    .addClass('btn-warning')
                    .find('.fa').removeClass('fa-search').addClass('fa-bug');
            } else {
                if (json.data.urls.view.auto) {
                    $('.action-preview')
                        .attr('onclick', "handlerShowDocument('"
                            +json.data.urls.view.auto+"', 'document-"+json.data.id
                            +"')")
                        .prop("disabled", false).removeAttr('disabled')
                    .removeClass('btn-warning').addClass('btn-default')
                    .find('.fa').removeClass('fa-bug').addClass('fa-search');
                }
                if (json.data.urls.download.odf || json.data.urls.download.xml) {
                    $('.action-download.type-odf')
                        .attr('download', json.data.filenames.odf || json.data.filenames.xml)
                        .attr('href', json.data.urls.download.odf || json.data.urls.download.xml)
                        .prop("disabled", false).removeAttr('disabled');
                }
                if (json.data.urls.download.pdf) {
                    $('.action-download.type-pdf')
                        .attr('download', json.data.filenames.pdf)
                        .attr('href', json.data.urls.download.pdf)
                        .prop("disabled", false).removeAttr('disabled');
                }
            };
            // If user can remove this report
            if (json.data.has_remove) {
                $('.action-remove')
                    .attr('onclick', "handlerRemoveDocument("+json.data.id+")")
                    .prop("disabled", false).removeAttr('disabled');
            } else {
                $('.action-remove').removeAttr('onclick')
                    .prop("disabled", true).attr('disabled', 'disabled');
            };

            // TODO: animation or 1-2 seconds after
            $pbar.removeClass('progress-bar-striped active');
    
            $('.action-recreate-report').prop("disabled", false).removeAttr('disabled');

            if (window.REPORT.create_force) {
                $('.action-create-report:visible').hide();
                $('.action-recreate-report:hidden').show();
            } else {
                $('.action-create-report').prop("disabled", true).attr('disabled', 'disabled');
            };
        } else if (now >= max){
            // report not ready and count request to server >= maximum request
            $pbar.addClass('progress-bar-striped active');
        } else {
            // report not ready
            handlerSetProgress(TIMEOUT_PROGRESS + now);
        };
    };

    var jqxhr = jsonAPI(args, cb);
    return jqxhr;
};

/* Обработчик запуска ожидания создания отчёта */
function handlerStartProgress() {
    $('.action-create-report').prop("disabled", true);
    $('.progress .progress-bar')
        .attr('aria-valuemax', window.REPORT.timeout || TIMEOUT_PROGRESS)
        .attr('aria-valuenow', 0).css('width', '0%');
    
    window.REPORT.process = setInterval(function () {
        handlerCheckProcess();
    }, window.TIMEOUT_PROGRESS);
};

/* Обработчик удаления отчёта */
function handlerRemoveDocument(id, refresh) {
    if (id) {
        var args = {
                'method': 'reportapi.document_delete',
                'id': id,
            },
            success = function() {
                $('#div-document-'+id).remove();
                $('#view-document-place').hide();
                if (refresh) window.location.reload()
                else handlerAfterChanges();
            };
        new jsonAPI(args, success);
    };
    
};

// События

/* Обработчик события создания отчёта */
function eventCreateReport(event) {
    handlerCreateReport();
    event.preventDefault();
};

/* Обработчик события пересоздания отчёта */
function eventRecreateReport(event) {
    handlerCreateReport(true);
    event.preventDefault();
};

/* Обработчик события удаления отчёта */
function eventRemoveDocument(event) {
    var id = null;
    handlerRemoveDocument(id);
    event.preventDefault();
};

////////////////////////////////////////////////////////////////////////
//                    Обработчики типов фильтров                      //
////////////////////////////////////////////////////////////////////////

/* Обработчик установки поиска-выбора для фильтров объектов */
function handlerSetSelectizers(filter) {
    var $box = $('#valuebox-'+filter.name);

    if ($box.size() <1) return false;

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
                        if (query.length <=3) {
                            return callback();
                        };
                    };

                    var args = {
                            'method': "reportapi.object_search",
                            'section': window.REPORT.section || null,
                            'name': window.REPORT.name,
                            'filter_name': filter.name,
                            'query': query,
                        },
                        success = function(res) {
                            callback(res.data.object_list);
                        };
                    new jsonAPI(args, success);
                },
                onChange: function(value) {
                    if (filter.condition == 'range' && (!value || value.length != 2)) {
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

    var other = $box.find('select[data-type="choice"],\
                      select[data-type="month"],\
                      select[data-type="weekday"],\
                      select[data-type="period"]');
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
                    if (filter.condition == 'range' && (!value || value.length != 2)) {
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

    return true;
};

/* Обработчик установки datetimepicker для input */
function handlerSetDatetimePickers(filter) {
    if (!filter || !(filter.type in {'datetime':'','date':'','time':''})) return false;
    var args = {
            lang: LANGUAGE_CODE,
            format: filter.format,
            timepicker: true,
            datepicker: true,
            mask: filter.use_mask,
        };

    if (filter.type == 'datetime') {
        args.formatDate = filter.formatDate;
        args.formatTime = filter.formatTime;
        args.onChangeDateTime = function(dt, $input) {
            /* сохраняем время так, как будто браузер находится в той-же
             * временной зоне, что и сервер.
             */
            var val;
            if (filter.use_tz) {
                dt.setMinutes(dt.getMinutes() - (dt.getTimezoneOffset() - SERVER_TZ_OFFSET));
                val = dt.toISOString();
            } else {
                val = ''+dt.getFullYear()+'-'+(dt.getMonth()+1)+'-'+dt.getDate()
                     +'T'+dt.getHours()+':'+dt.getMinutes()+':'+dt.getSeconds()
                     +'.'+dt.getMilliseconds();
            }
            $input.data('server_value', val);
        }
    } else if (filter.type == 'time') {
        args.formatTime = filter.format;
        args.datepicker = false;
        args.onChangeDateTime = function(dt, $input) {
            /* сохраняем время в понятном серверу формате.*/
            $input.data('server_value',
                ''+dt.getHours()+':'+dt.getMinutes()+':'+dt.getSeconds()
                +'.'+dt.getMilliseconds());
        }
    } else {
        args.formatDate = filter.format;
        args.timepicker = false;
        args.onChangeDateTime = function(dt, $input) {
            /* сохраняем дату в понятном серверу формате.*/
            dt.setMinutes(dt.getMinutes() - (dt.getTimezoneOffset() - SERVER_TZ_OFFSET));
            $input.data('server_value',
                ''+dt.getFullYear()+'-'+(dt.getMonth()+1)+'-'+dt.getDate());
        }
    };

    if (filter.condition == 'range') {
        var args1 = {}, args2 = {},
            $input1 = $('#value-'+ filter.name +'-range1'),
            $input2 = $('#value-'+ filter.name +'-range2');

        $.extend(true, args1, args);
        $.extend(true, args2, args);

        // TODO: сделать ограничение для datetime
        if (filter.type == 'date') {
            args1.onShow = function(ct){
                this.setOptions({ maxDate: $input2.data().server_value ? $input2.val() : false })
            };
            args2.onShow = function(ct){
                this.setOptions({ minDate: $input1.data().server_value ? $input1.val() : false })
            }
        }

        $input1.datetimepicker(args1);
        $input2.datetimepicker(args2);
    } else {
        $('#value-'+ filter.name).datetimepicker(args);
    }

    return true;
};

/* Обработчик проверки обязательных фильтров */
function handlerCheckRequiredValue() {

    var completed = true;
    $.each(REPORT.filters, function(key, item) {
        if (item.required) {
            if (item.value === null || item.value === undefined) {
                completed = false;
            } else if (item.condition == 'range' &&
                (item.value.length < 2 || item.value[0] === null || item.value[1] === null)) {
                completed = false;
            };
        }
    });
    if (completed) {
        $('.action-create-report').prop("disabled", false).removeAttr("disabled");
    } else {
        $('.action-create-report').prop("disabled", true).attr('disabled', 'disabled');
    };
    return completed;
};

/* Постобработчик изменения значения или условия фильтра */
function handlerAfterChanges() {
    if (window.REPORT.process) {
        clearInterval(window.REPORT.process);
        window.REPORT.id = null;
        window.REPORT.process = null;
    };
    handlerSetProgress(0);
    $('.action-create-report, .action-preview, .action-download, .action-remove')
        .attr('disabled', 'disabled');
    $('.action-recreate-report:visible').hide();
    $('.action-create-report:hidden').show();
    handlerCheckRequiredValue();
};


// События

/* Обработчик события изменения значения фильтра */
function eventChangeValue(event) {
    var value = this.value,
        data = $(this).data(),
        server_value = data.server_value,
        filter = REPORT.filters[this.name],
        test_datetime = function(objects) {
            var test = true;
            $.each(objects, function(i, v){
                if (!v || v.indexOf('_') >= 0) { test = false }
            })
            return test 
        };

    if (filter.type == 'boolean') $('#valuebox-'+filter.name).html('');

    if (this.type == 'radio') {
        // Для радио-кнопок с булевыми значениями
        filter.value = (value == 'true') ? true : (value == 'false') ? false : null;
        if (server_value != undefined) filter.server_value = filter.value;
    } else if (filter.condition == 'range' && filter.type in {'datetime':'','date':'','time':''}) {
        // Для datetimepickers с условием диапазона
        var other, other_value;
        if (this.id.match(/.*-range1/g)) {
            other = $('#value-'+ filter.name +'-range2');
            other_value = other.val();
            filter.value = test_datetime([other_value, value]) ? [value, other_value] : null;
            filter.server_value = test_datetime([other_value, value]) ? [server_value, other.data().server_value] : null;
        } else {
            other = $('#value-'+ filter.name +'-range1');
            other_value = other.val();
            filter.value = test_datetime([other_value, value]) ? [other_value, value] : null;
            filter.server_value = test_datetime([other_value, value]) ? [other.data().server_value, server_value] : null;
        }
    } else {
        filter.value = value || null;
        if (server_value != undefined) filter.server_value = server_value;
    };

    handlerAfterChanges();
};

/* Обработчик события изменения условия фильтра
 * 
 * TODO: сделать установку дефолтных значений для даты-времени
 * 
 */
function eventConditionChange(event) {

    var filter = REPORT.filters[$(this).data()['name']],
        prev_condition = filter.condition,
        prev_value     = filter.value,
        prev_server_value = filter.server_value;

    filter.condition = this.value || null;


    if (!filter.condition) {
        // Сброс условия
        filter.value = null;
        if (filter.server_value != undefined) filter.server_value = null;

    } else if (filter.condition in {'isnull':0, 'empty':0}) {
        // Для условия "пусто" значение по-умолчанию истинно
        filter.value = true;

    } else if (prev_value === true || prev_value === false || prev_value === null || prev_value === undefined) {
        // Предыдущего значения небыло или стояло одно из условий: 'isnull', 'empty'
        filter.value = null;
        if (filter.server_value != undefined) filter.server_value = null;

    } else if (filter.type in {'object':0, 'choice':0, 'month':0, 'weekday':0, 'period':0}) {
        // Объекты и списки выбора сбрасываются потому, что не найдено
        // решение их установки в библиотеке selectize
        filter.value = null;

    } else if (filter.condition in {'range':0,'in':0}) {
        // Для этих условий заполняем одним значением
        if (!(prev_condition in {'range':0,'in':0})) {

            filter.value = (filter.condition == 'range') ?
                    [prev_value, prev_value] : [prev_value];

            if (filter.server_value != undefined) {
                filter.server_value = (filter.condition == 'range') ?
                    [prev_server_value, prev_server_value] : [prev_server_value];
            }

        } else if (prev_condition == 'in' && filter.condition == 'range') {

            filter.value = prev_value.slice(0, 2);

            if (filter.value.length < 2) { filter.value[1] = filter.value[0] }

            if (filter.server_value != undefined) {

                filter.server_value = prev_server_value.slice(0, 2);

                if (filter.server_value.length < 2) { filter.server_value[1] = filter.server_value[0] }
            }
        } /* else {  prev_condition == 'range' && filter.condition == 'in'  } */
    } else {
        // Любые другие условия
        if (prev_condition in {'range':0,'in':0}) {

            filter.value = prev_value ? prev_value[0] : null;

            if (filter.server_value != undefined) {
                filter.server_value = prev_server_value ? prev_server_value[0] : null;
            }
        }
    };

    var html = TEMPLATES.filter({ data: filter });

    $('#valuebox-'+filter.name).html(html);

    handlerSetSelectizers(filter);
    handlerSetDatetimePickers(filter);

    handlerAfterChanges();

    return true;
};

/* Проверка события нажатия клавиши управления браузером */
function keyDownIsControl(event) {
    if ((event.which == 8) // backspace
        || (event.which == 9) // tab
        || (event.which == 13) // enter
        || (event.which == 27) // escape
        || (event.which >= 33 && event.which <= 46) // Page Up - Delete
        || (event.which >= 112 && event.which <= 145) // F1 - ScrollLock
    ) { return true }
    return false;
};

/* Обработчик события нажатия клавиши на поле ввода чисел */
function eventKeyDownOnNumber(event) {

    var adddot = function(event) {
        value = event.target.value || '';
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

/* Обработчик прогрессбара */
function handlerSetProgress(now) {
    now = now || 0;
    var $pbar = $('.progress .progress-bar'),
        max = Number($pbar.attr('aria-valuemax')) || 100,
        width = (now / max) * 100;
    width = width > 100 ? 100 : width;
    $pbar.attr('aria-valuenow', now).css('width', width +'%');
};

/* Обработчик просмотра отчёта */
function handlerShowDocument(href, name, inwindow) {
    if (inwindow) {
        var win = window.open(href, name, 'height=500,width=800,resizable=yes,scrollbars=yes');
        win.focus();
    } else {
        var $place  = $('#view-document-place'),
            html = '<iframe class="embed-responsive-item" src="'
                   +href
                   +'" allowfullscreen webkitallowfullscreen></iframe>';
        if ($place.size() == 0) {
            $('#view-'+name).toggle();
            $('#view-'+name+':visible .embed-responsive').html(html);
        } else {
            $place.show().find('.embed-responsive').html(html);
        }
    }
};

/* Обработчик установки шаблонов */
function handlerTemplates() {

    TEMPLATES.alert  = _.template($('#underscore-alert').html());
    TEMPLATES.filter = _.template($('#underscore-filter').html());

    return true;
};

/* Обработчик установки биндингов для элементов */
function handlerBindinds() {

    // Биндинг на сокрытие алерта
    $('body').on('click', 'button.close[data-dismiss="alert"]', 
        function () {$('#alert-place').css('z-index', '-1000');});

    $('body').on('change', 'select[id^="condition-"]', eventConditionChange);
    $('body').on('keydown', 'input[data-validate="number"]', eventKeyDownOnNumber);
    $('body').on('change', 'input[id^="value-"]', eventChangeValue);

    $('body').on('click', '.action-create-report', eventCreateReport);
    $('body').on('click', '.action-recreate-report', eventRecreateReport);

    return true;
};

////////////////////////////////////////////////////////////////////////
//                            ИСПОЛНЕНИЕ                              //
////////////////////////////////////////////////////////////////////////

/* Выполнение чего-либо после загрузки страницы */
$(document).ready(function($) {

    // Инициализация шаблонов Underscore
    handlerTemplates();

    // Инициализация для Bootstrap и плагинов
    $("alert").alert();
    $(".dropdown-toggle").dropdown();

    // Установка биндингов для элементов
    handlerBindinds();

});
