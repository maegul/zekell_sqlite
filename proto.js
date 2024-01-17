console.log('hello world')


// var count = 0

// var action_but = document.querySelector('#but_fetch')
// var content = document.querySelector('#content')

// console.log('button element?', action_but)

// action_but.addEventListener(
// 	'click',
// 	() => {
// 		count = count + 1
// 		// content.innerHTML = count

// 		fetch("http://0.0.0.0:5000/jsontest")
// 			.then((response) => response.json())
// 			.then((body) => {
// 				console.log(body)
// 				// just add more inner divs?
// 				content.innerHTML = content.innerHTML + '<br>' + count + ': ' + body['content']
// 			}
// 			)
// 			.catch((error) => console.log(error));

// 	}
// )

// > Utils

function removeAllChildNodes(node) {
	while (node.firstChild) {
		node.removeChild(node.firstChild)
	}
}

// > Template functions

function add_preview_event_listener(button, note_id){

	button.addEventListener(
		'click',
		function (event) {
			// const note_id = value.parentNode.getAttribute('data-note-id')

			const url_params = new URLSearchParams({id: parseInt(note_id)})
			fetch("http://0.0.0.0:5000/note?" + url_params)
			.then(response => response.json())
			.then(data => {
				// Handle the response data and update the page
				const preview = document.body.appendChild(document.createElement('div'))
				preview.innerHTML = data['body']
			})
			.catch(error => {
				console.error("Error:", error);
			});
		}
	)

}

function make_result_row(data) {

	const template = document.querySelector('#template_result_row')

	const result = template.content.cloneNode(true)
	const result_cont = result.querySelector('div')
	const result_text = result.querySelector('p')
	const result_preview_button = result.querySelector('button')

	result_cont.setAttribute('data-note-id', data['id'])
	result_text.innerHTML = `${data['title']} (${data['id']})`
	add_preview_event_listener(result_preview_button, data['id'])

	return result
}


// > Main

function update_search_results(data){
	// console.log('search data', data)
	const search_results_div = document.getElementById('search_results_div')
	removeAllChildNodes(search_results_div)

	for (var i = data.length - 1; i >= 0; i--) {

		let result_data = data[i]
		const result_row = make_result_row(result_data)
		search_results_div.appendChild(result_row)
	}

}

document.getElementById("general_query_form")
	.addEventListener("submit", function (event) {
		event.preventDefault();

		const formData = new FormData(event.target);

		// console.log('form data', formData)

		fetch("http://0.0.0.0:5000/general_search", {
			method: "POST",
			body: formData,
		})
		.then(response => response.json())
		.then(data => {
			// Handle the response data and update the page
			update_search_results(data);
		})
		.catch(error => {
			console.error("Error:", error);
		});
});



// > Encoding queries

// >> Example from GPT

// const query = "this is:; a test";
// const encodedQuery = encodeURIComponent(query);

// const apiUrl = "http://your-api-url/general_search?query=" + encodedQuery;

// // Now, you can use the apiUrl in your AJAX request or wherever you are making the HTTP request.

