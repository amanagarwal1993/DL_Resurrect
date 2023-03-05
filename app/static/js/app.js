var model = {
    current_fragment_id: 1,
    
    init: function(num) {
        localStorage.clear();
        model.current_fragment_id = num;
    },
    
};

var sharktopus = {
    
    init: function(num, comment_icon_url) {
        model.init(num);
        view.list_posts();
        view.setup_fragments(comment_icon_url, num);
        if (num == 0) {
            num = 1;
        }
        view.update_current_fragment(num);
        view.expand_text();
    },
    
    get_current_fragment: function() {
        return model.current_fragment_id;
    },
    
    set_current_fragment: function(frag_id) {
        model.current_fragment_id = frag_id;
        view.unhighlight_fragments();
        view.highlight_fragment(frag_id);
        view.update_form(frag_id);
        view.list_posts();
    },
      
};

var view = {
    
    setup_fragments: function(comment_icon_url, frag_id=0) {
        $('.image').on('click', function() {
            var frag_id = parseInt($(this).attr('id').substring(9), 10);
            view.update_current_fragment(frag_id);
        });
        
        $('.comment-icon').attr('src', comment_icon_url);
        
        // Don't scroll if fragment is 0, but default to 1
        if (frag_id == 0) {
            var first_fragment = document.getElementById('fragment-1');
            
        }
        else if (frag_id > 0) {
            var first_fragment = document.getElementById('fragment-' + frag_id.toString());
            first_fragment.scrollIntoView();
        };
        
    },
    
    list_posts: function() {
        $('.prior-post').hide();
        
        fragment_id = sharktopus.get_current_fragment();
        
        // find all posts with that new paragraph id
        var relevant_posts_selector = ".para-" + fragment_id.toString();
        
        // remove display: None property
        $(relevant_posts_selector).show();
    },
    
    update_current_fragment: function(frag_id) {
        sharktopus.set_current_fragment(frag_id);
    },
    
    highlight_fragment: function(frag_id) {
        
        if (frag_id==0) {
            frag_id = 1;
        }
        
        $('#fragment-' + frag_id.toString()).css('background-color', '#7fff00');
    },
    
    unhighlight_fragments: function() {
        $('.image').css('background-color', "");
    },
    
    update_form: function(frag_id) {
        if (frag_id == 0) {
            frag_id = 1;
        }
        
        $('#form_fragment').val(frag_id);
        
        if (frag_id % 5 == 0) {
           $('#form_fragment_label').css('color', '#0066ff'); 
        }
        
        if (frag_id % 5 == 1) {
           $('#form_fragment_label').css('color', '#0099ff'); 
        }
        
        if (frag_id % 5 == 2) {
           $('#form_fragment_label').css('color', '#6699ff'); 
        }
        
        if (frag_id % 5 == 3) {
           $('#form_fragment_label').css('color', '#5c00e6'); 
        }
        
        if (frag_id % 5 == 4) {
           $('#form_fragment_label').css('color', '#00b36b'); 
        }
        
    },
    
    expand_text: function() {
        $('.read-more').on('click', function() {
            var post_id = $(this).attr('id').substring(7);
            var dots = document.getElementById("dots-" + post_id);
            var moreText = document.getElementById("moretext-" + post_id);
            var btnText = document.getElementById("expand-" + post_id);

            if (dots.style.display == "none") {
                dots.style.display = "inline";
                btnText.innerHTML = "Show more";
                moreText.style.display = "none";
            } else {
                dots.style.display = "none";
                btnText.innerHTML = "Show less";
                moreText.style.display = "inline";
            } 
        });
    }
    
}

sharktopus.init(first_fragment, comment_icon_url);