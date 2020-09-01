
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
         addImages(myJson, this.value.toLowerCase());
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

  if ('exts' in obj) {
    const e = $('#files')
    const links = obj['exts'].reduce(function(acc, ext) {
      acc.push('<a href="images/' + name + '.' + ext + '">' + ext + '</a>')
      return acc
    }, [])
    html.push('[' + links.join(', ') + ']')
  }

  if ('author' in obj) {
    html.push(obj['author'])
  }

  if ('license' in obj) {
    html.push(obj['license'])
  }

  return '"' + (obj['title'] || name) + '"<br>' + html.join(' | ');
}

function addImages(myJson, filter) {
  // remove all images
  $('#imagesContainer').textContent = ""

  for (const [name, obj] of Object.entries(myJson)) {
    // filter images
    if (!match(filter, name, obj)) {
      continue
    }

    const div = document.createElement('figure')
    const img = document.createElement('img')
    const p = document.createElement('figcaption')
    div.appendChild(img)
    div.appendChild(p)

    p.innerHTML = getUnderline(name, obj)
    div.classList.add('container');

    //const img = document.createElement('img');
    img.setAttribute('data-lazy-name', name);
    img.classList.add('lazy-loading');
    $('#imagesContainer').appendChild(div);
  }

  lazyTargets = document.querySelectorAll('.lazy-loading');
  lazyTargets.forEach(e => lazyLoad(e, myJson));
}

function get_preferred_ext(exts) {
  // get preferred image extensions
  for (const ext of ["png", "jpg", "svg", "gif", "tif", "pdf"]) {
    if (exts.includes(ext)) {
      return ext
    }
  }
  return exts[0]
}

function lazyLoad(target, myJson) {
  const obs = new IntersectionObserver((entries, observer) => {
    entries.forEach(entry => {
      if (entry.isIntersecting) {
        const img = entry.target
        const name = img.getAttribute('data-lazy-name')
        const path = 'images/' + name + '.' + get_preferred_ext(myJson[name]["exts"])

        img.setAttribute('src', encodeURI(path))
        img.classList.add('fadeIn')

        observer.disconnect()
      }
    });
  });
  obs.observe(target);
}
