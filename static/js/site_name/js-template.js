/**
 * Example Javascript Module Pattern
 */
var mymodule = function($) {

    var my_private_var = null;

    function private_method(li_container) {
        // private method code
    }

    return {

        public_property: null,

        public_method: function() {
            var self = this;
            // code...
        },

        init: function(options) {
            // init code...
        }

    };

}(jQuery);