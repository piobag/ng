{% if 'adm' in roles %}
  const auth_groups = {{ config['AUTH_ROLES']|tojson|safe }}
{% elif 'settings' in roles %}
  const auth_groups = {{ config['AUTH_ROLES']|tojson|safe }}
{% endif %}

const est_civis = {{ config['EST_CIVIS']|tojson|safe }}

const $ = ( id ) => document.getElementById( id )
const csrf_token = "{{ csrf_token() }}"
const spinner_b = '<div class="d-flex h-100 align-items-center justify-content-center"><div class="text-center spinner-border spinner-border-sm text-dark" role="status"></div></div>'
const spinner_w = '<div class="d-flex h-100 align-items-center justify-content-center"><div class="text-center spinner-border spinner-border-sm text-ligth" role="status"></div></div>'
const currency_br = { minimumFractionDigits: 2 , style: 'currency', currency: 'BRL' }
const default_per_page = 5

const pagination = (total, f, start, perpage, filter=false) => {
  let page = 1
  let pages = Array.from(Array(Math.floor((total-1)/perpage)+1)).map(p => page++)
  const totalPages = Math.ceil(total/perpage)
  let current_page = Math.floor(start/perpage)+1
  if (pages.length > 6 ) {
    if (current_page < 5) {
      pages = [1, 2, 3, 4, 5, '...', pages.length]
    } else if (current_page > pages.length - 4 ) {
        pages = [1, '...', pages.length-4, pages.length-3, pages.length-2, pages.length-1, pages.length]
    } else {
        pages = [1, '...', current_page-2, current_page-1, current_page, current_page+1, current_page+2, '...', pages.length]
    }
  }
  return `{% include 'pagination.html' %}`
}

let search_timeout = null
function search(that){
  that.value = that.value.toUpperCase()
  clearTimeout(search_timeout);
  search_timeout = setTimeout(function() {
  }, 1000)
}

function mask_value(that) {
    let value = that.value
    value = value + ''
    value = parseInt(value.replace(/[\D]+/g,''))
    value = value + ''
    if (value.length == 1) {
        value = value.replace(/([0-9]{1})$/g, "0,0$1")
    } else {
        value = value.replace(/([0-9]{2})$/g, ",$1")
    }
    if (value.length > 6) {
        value = value.replace(/([0-9]{3}),([0-9]{2}$)/g, ".$1,$2")
    } else if (/^,[0-9]{2}$/.test(value)) {
        value = '0' + value
    }
    that.value = value
}

function mask_upcase(that){
  that.value = that.value.toUpperCase()
}

function mask_tel(o, f) {
    setTimeout(function() {
      let v = mtel(o.value)
      if (v != o.value) {
        o.value = v
      }
    }, 1)
}
  
function mtel(v) {
    let r = v.replace(/\D/g, "")
    r = r.replace(/^0/, "")
    if (r.length > 10) {
      r = r.replace(/^(\d\d)(\d{5})(\d{4}).*/, "($1) $2-$3")
    } else if (r.length > 5) {
      r = r.replace(/^(\d\d)(\d{4})(\d{0,4}).*/, "($1) $2-$3")
    } else if (r.length > 2) {
      r = r.replace(/^(\d\d)(\d{0,5})/, "($1) $2")
    } else {
      r = r.replace(/^(\d*)/, "$1")
    }
    return r
}

var loop_files = (files) => new Promise(resolve => {
  setTimeout(function() {
      files.forEach(file => {
          if (file.readyState != 2) {
              loop_files(files)
          }
      })
      resolve()
  }, 1000)
})

function add_payment_percent(num, percentage){
  let result = num * (percentage / 100);
  return parseFloat(result.toFixed(2));
}




