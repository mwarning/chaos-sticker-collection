
function $(query) {
  return document.querySelector(query);
}

window.onload = () => {
  fetch('data.json')
    .then(function(response) {
      return response.json();
    })
    .then(function(myJson) {
      // Display images
      addImages(myJson, "");

      // Remove loading spinner
      document.getElementById('lds-roller').remove();

      $('#filter').oninput = function () {
        const filter = this.value.toLowerCase()
        // Add filter to URL
        if (filter) {
          history.replaceState(null, null, document.location.href.split("?")[0] + "?filter=" + encodeURIComponent(filter));
        } else {
          history.replaceState(null, null, document.location.href.split("?")[0]);
        }
        addImages(myJson, filter);
      }

      // Apply filter from URL
      const url_params = new URLSearchParams(window.location.search);
      const filter = url_params.get("filter") || "";
      if (filter) {
        $('#filter').value = filter
        addImages(myJson, filter);
      }
    })
    .catch(err => {
      console.log(err);
    });
};

// match against all image meta data
function match(words, name, obj) {
  if (words.length == 0)
    return true

  function single_match(word) {
    if (name.toLowerCase().indexOf(word) !== -1)
      return true

    for (const [key, val] of Object.entries(obj)) {
      if (typeof val === 'string') {
        if (val.toLowerCase().indexOf(word) !== -1)
          return true
      } else {
        if (val.indexOf(word) !== -1)
          return true
      }
    }
    return false
  }

  // split into words
  for (const word of (words.match(/[^\s,]+/g) || [])) {
    if (!single_match(word))
      return false
  }

  return true
}

function getUnderline(name, obj) {
  let html = []

  function encodeObj(name, obj) {
    let str = "name=" + encodeURIComponent(name)
    for (let key in obj) {
      str += "&" + encodeURIComponent(key) + "=" + encodeURIComponent(obj[key])
    }
    return str
  }

  html.push('<a href="images/' + encodeURIComponent(name) + '/index.html">files</a>')

  if ('author' in obj) {
    if ('link' in obj) {
      html.push('<a href="' + obj['link'] + '">' + obj['author'] + '</a>')
    } else {
      html.push(obj['author'])
    }
  } else {
    if ('link' in obj) {
      html.push('<a href="' + obj['link'] + '">source</a>')
    }
  }

  if ('license' in obj) {
    html.push(obj['license'])
  }

  // edit link
  //html.push('<a class="edit" href="submit.html?' + encodeObj(name, obj) + '" alt="edit">&#x270D;</a>')

  return '"' + (obj['title'] || name) + '"<br>' + html.join(' | ');
}

function addImages(myJson, filter) {
  let count = 0

  // remove all images
  $('#imagesContainer').textContent = ""

  for (const [name, obj] of Object.entries(myJson)) {
    // filter images
    if (!match(filter, name, obj)) {
      continue
    }

    const img = document.createElement('img')
    img.setAttribute('data-lazy-name', name)
    img.classList.add('lazy-loading')

    const div = document.createElement('figure')
    div.classList.add('container')
    div.appendChild(img)

    $('#imagesContainer').appendChild(div);

    count += 1
  }

  lazyTargets = document.querySelectorAll('.lazy-loading');
  lazyTargets.forEach(e => lazyLoad(e, myJson));
  $('#count').innerText = count
}

function lazyLoad(target, myJson) {
  const obs = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target
        const name = img.getAttribute('data-lazy-name')
        const src = 'images/' + encodeURIComponent(name) + '/preview.webp'

        const p = document.createElement('figcaption')
        p.innerHTML = getUnderline(name, myJson[name])
        img.parentNode.appendChild(p)

        img.setAttribute('src', src)
        img.classList.add('fadeIn')

        observer.disconnect()
      }
    });
  });
  obs.observe(target);
}
