console.log('hello world')


var count = 0

var action_but = document.querySelector('#but_fetch')
var content = document.querySelector('#content')

console.log('button element?', action_but)

action_but.addEventListener(
	'click',
	() => {
		count = count + 1
		// content.innerHTML = count

		fetch("http://0.0.0.0:5000/jsontest")
			.then((response) => response.json())
			.then((body) => {
				console.log(body)
				// just add more inner divs?
				content.innerHTML = content.innerHTML + '<br>' + count + ': ' + body['content']
			}
			)
			.catch((error) => console.log(error));

	}
)

