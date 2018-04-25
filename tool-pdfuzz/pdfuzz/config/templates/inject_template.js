var Plugin = function (name, description, filename, version) {
    this.name = name || "";
    this.description = description || "";
    this.filename = filename || "";
    this.version = version || "";
};
var PluginArray = function () {
    this.length = 0;
    this.refresh = function () {return true;};
};

PluginArray.prototype['@@iterator'] = function() {
    var index = 0,
        self = this;
    return {
        next: function () {
            if (index >= self.length) {
                return {done: true};
            } else {
                return {
                    value: self[index++],
                    done: false
                }
            }
        }
    }
};

PluginArray.prototype.addPlugin = function (plugin) {
    this[this.length] = plugin;
    this[plugin.name] = plugin;
    this.length++;
};

var MimeType = function (type, suffixes, description) {
    this.type = type || "";
    this.suffixes = suffixes || "";
    this.description = description || "";
};
var MimeTypeArray = function () {
    this.length = 0;
    this.refresh = function () {return true;};
};

MimeTypeArray.prototype['@@iterator'] = function() {
    var index = 0,
        self = this;
    return {
        next: function () {
            if (index >= self.length) {
                return {done: true};
            } else {
                return {
                    value: self[index++],
                    done: false
                }
            }
        }
    }
};

MimeTypeArray.prototype.addMimeType = function (mimetype) {
    this[this.length] = mimetype;
    this[mimetype.name] = mimetype;
    this.length++;
};

return (function() {
    Date.prototype.getTimezoneOffset = function() {
        return {{ timezoneoffset }};
    };
    new_navigator = JSON.parse(JSON.stringify(window.navigator));
    new_navigator.javaEnabled = function() {return false;};
    
    new_navigator.plugins = new PluginArray();
    {% for new_plugin in plugins %}
        new_navigator.plugins.addPlugin({{ new_plugin }});
    {% endfor %}

    new_navigator.mimeTypes = new MimeTypeArray();
    {% for new_mimetype in mimetypes %}
        new_navigator.mimeTypes.addMimeType({{ new_mimetype }});
    {% endfor %}

    {% for key in navigator_obj %}
        {% if navigator_obj[key] is string and "languages" not in key %}
            new_navigator.{{ key }} = '{{ navigator_obj[key] }}';
        {% else %}
            new_navigator.{{ key }} = {{ navigator_obj[key] }};
        {% endif %}
    {% endfor %}

    window.navigator = new_navigator;
    window.screen = {
        {% for key in screen_obj %}
            {% if screen_obj[key] is string %}
                {{ key }} : '{{ screen_obj[key] }}',
            {% else %}
                {{ key }} : {{ screen_obj[key] }},
            {% endif %}
        {% endfor %}
    };
})();