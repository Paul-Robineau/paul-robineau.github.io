function setCookie(name, value, exdays) {
  var d, expires
  exdays = exdays || 1
  d = new Date()
  d.setTime(d.getTime() + exdays * 86400000)
  expires = 'expires=' + d
  document.cookie = name + '=' + value + '; ' + expires + '; path=/'
}

function getCookie(name) {
  var c
  cookies = document.cookie.split(';')
  for (var i = 0; i < cookies.length; i++) {
    c = cookies[i].split('=')
    if (c[0] == name) {
      return c[1]
    }
  }
  return ''
}

var standardLanguage = {}
var standardLanguageLoaded = false

function loadJSON(file, callback) {
  var xobj = new XMLHttpRequest()
  xobj.overrideMimeType('application/json')
  xobj.open('GET', file, true) // Replace 'my_data' with the path to your file
  xobj.onreadystatechange = function() {
    if (xobj.readyState == 4 && xobj.status == '200') {
      // Required use of an anonymous callback as .open will NOT return a value but simply returns undefined in asynchronous mode
      callback(JSON.parse(xobj.responseText))
    }
  }
  xobj.send(null)
}

function chooseLanguage(lang, loadStandard = false) {
  setCookie('lang', lang, 7)
  if (lang === 'fr-FR') {
    loadJSON('/js/fr.json', function(data) {
      let hasLoaded = false
      Object.keys(data).forEach(key => {
        const el = document.getElementById(key)
        if (loadStandard && !standardLanguageLoaded) {
          if (el && el.innerHTML) {
            standardLanguage[key] = el.innerHTML
            hasLoaded = true
          }
        }
        if (el && el.innerHTML) el.innerHTML = data[key]
      })
      if (hasLoaded) standardLanguageLoaded = true
    })
  } else {
    if (standardLanguageLoaded) {
      Object.keys(standardLanguage).forEach(key => {
        const el = document.getElementById(key)
        el.innerHTML = standardLanguage[key]
      })
    }
  }
}

if (!document.cookie) {
  if (navigator.language === 'fr-FR') {
    chooseLanguage('fr-FR', true)
  }
} else {
  const lang = getCookie('lang')
  if (lang !== '') {
    if (lang === 'fr-FR') {
      chooseLanguage('fr-FR', true)
    } else {
      console.log('lang', lang)
    }
  }
}
