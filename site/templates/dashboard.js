const linkList = document.querySelectorAll('.nav_link')
const sectionList = document.querySelectorAll("section")
const sec_info = $('sec_info')

function selectLink(){
    linkList.forEach(l=> l.classList.remove('active'))
    this.classList.add('active')

    sectionList.forEach(s => {
      if (s.id == this.id.split('_')[1]) {
        s.style.display = 'grid'
      } else { s.style.display = 'none' }
    })
}
linkList.forEach(l=> l.addEventListener('click', selectLink))

$('user-toggle').addEventListener('click', () => {get_profile(); profile_modal.show()})

document.addEventListener("DOMContentLoaded", (event) => {
  const toggle = $('header-toggle')
  const nav = $('nav-bar')
  const bodypd = $('body-pd')
  if(toggle && nav && bodypd){
    toggle.addEventListener('click', ()=>{
      // show navbar
      nav.classList.toggle('show_nav')
      // change icon
      toggle.classList.toggle('btn-arrow')
      // add padding to body
      bodypd.classList.toggle('body-pd')
    })
  }
  // toggle.click()

  {% if 'audit' in roles %}
    $('show_dash').click()
  {% elif 'fin' in roles %}
    $('show_finance').click()
  {% elif 'itm' in roles %}
    $('show_onr').click()
  {% elif 'ri' in roles %}
    $('show_attend').click()
  {% elif 'settings' in roles %}
    $('show_settings').click()
  {% elif 'ng' in roles %}
    $('show_vacation').click()
  {% elif 'adm' in roles %}
    $('show_finance').click()
  {% endif %}
  })

function dashboard_search(that, event) {
  let api_url = ''
  let popoverCustom = ''
  api_url = `{{ url_for('attend.search') }}?text=${that.value}`
  fetch(api_url).then(response => response.json()).then(data => {
    let result = data['result']
    if (result) {
      let popoverContent = '<ul class="list-group">'
      result.forEach(function(result) {
        popoverCustom =  `<li id="pop_${result.attend}" onclick="open_attend_info('${result.attend}'); dashboard_Sclean()" style="color: var(--first-color);" class="list-group-item list-group-item-action">` + result.prot + '</li>'
        popoverContent += popoverCustom

      })
      popoverContent += '</ul>'
    
      let searchInput = document.getElementById('dashboard_search')
    
      // Remove o popover existente (se houver)
      let existingPopover = document.querySelector('.popover')
      if (existingPopover) {
        existingPopover.parentNode.removeChild(existingPopover);
      }
    
      // Cria o elemento popover
      let popover = document.createElement('div');
      popover.classList.add('popover');
      popover.innerHTML = popoverContent;
    
      // Define as propriedades do popover
      popover.setAttribute('role', 'tooltip');
      popover.style.display = 'block';
      popover.style.position = 'fixed';

      // Centraliza verticalmente
      let topPosition = searchInput.offsetTop + (searchInput.offsetHeight / 2) - (popover.offsetHeight / 2);
      popover.style.top = topPosition + 'px';

      // Centraliza horizontalmente
      let leftPosition = searchInput.offsetLeft + (searchInput.offsetWidth / 2) - (popover.offsetWidth / 2);
      popover.style.left = leftPosition + 180 + 'px';

      popover.style.top = searchInput.offsetTop + searchInput.offsetHeight - 38 + 'px';
  
      // top: 8px;
      // 38
      // left: 1390px;
      // 178
      // Insere o popover no documento
      document.body.appendChild(popover)
      if(result[0]){
        dashboard_search_enter(event, `${result[0].id}`)
      }
    } else { data['error'] ? alert(data['error']) : '' }
  }).catch(error => { alert(`{{ _('Error in API') }} ${api_url} | ${error}`) })

}

function dashboard_Sclean() {
  setTimeout(function() {
    $('dashboard_search').value = ''
  }, 3000)
}
  
function dashboard_filter(event, table) {
  event.preventDefault()
  if (event.key != 'Shift' && event.key != 'Control') { 
    setTimeout(function() {
      table
    }, 2000)
  }
}

function dashboard_search_enter(event, id) {
  event.preventDefault()
  if (event.key === 'Enter') { 
    let popover = document.querySelector(`#pop_${id}`)
    popover.click()
  }
}
  


// Fecha o popover ao clicar em qualquer lugar fora dele
document.body.addEventListener('click', function(e) {
  if (!e.target.matches('#dashboard_search')) {
    var popover = document.querySelector('.popover');
    if (popover) {
      popover.parentNode.removeChild(popover);
    }
  }
});

