console.log('hello world')

const base_url = "http://0.0.0.0:5000"

// > Utils

function removeAllChildNodes(node) {
	while (node.firstChild) {
		node.removeChild(node.firstChild)
	}
}

// > Template functions

function update_note_view(note_data) {
	const note_view = document.getElementById('zkl_note_view')

	const title = note_view.querySelector(".note_view_title")
	const body = note_view.querySelector(".note_view_body")
	removeAllChildNodes(title)
	// removeAllChildNodes(body)
	body.value = ""

	title.textContent = note_data['title']
	// body.textContent = note_data['body']
	body.value = note_data['body']
}

function add_preview_event_listener(button, note_id){

	button.addEventListener(
		'click',
		function (event) {
			// const note_id = value.parentNode.getAttribute('data-note-id')

			const url_params = new URLSearchParams({id: parseInt(note_id)})
			fetch(`${base_url}/note?` + url_params)
			.then(response => response.json())
			.then(data => {
				// Handle the response data and update the page
				update_note_view(data)
			})
			.catch(error => {
				console.error("Error:", error);
			});
		}
	)

}

function make_result_row(data) {

	const template = document.querySelector('#zkl_template_result_row')

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
	const search_results_div = document.getElementById('zkl_search_results_div')
	removeAllChildNodes(search_results_div)

	for (var i = data.length - 1; i >= 0; i--) {

		let result_data = data[i]
		const result_row = make_result_row(result_data)
		search_results_div.appendChild(result_row)
	}

}

document.getElementById("zkl_general_query_form")
	.addEventListener("submit", function (event) {
		event.preventDefault();

		const formData = new FormData(event.target);

		// console.log('form data', formData)

		fetch(`${base_url}/general_search`, {
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

