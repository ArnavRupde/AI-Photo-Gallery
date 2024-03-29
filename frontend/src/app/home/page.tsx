"use client"
import React from "react"
import {Gallery} from "react-grid-gallery"
import { useState, useEffect, FormEvent } from "react"

const IMAGE_STORAGE_PREFIX = "http://localhost:5000/image/"

interface CustomImage {
    image_description: string;
    image_path: string;
}

function generateImageElement(imageUrl: string) {
    return {
        src: imageUrl,
        original: imageUrl
    }
}

export default function Homepage() {
    const [images, setImages] = useState([])
    const [isLoading, setIsLoading] = useState<boolean>(false)
 
    async function onSubmit(event: FormEvent<HTMLFormElement>) {
        event.preventDefault()
        setIsLoading(true) // Set loading to true when the request starts
    
        try {
            console.log("Event currentTarget", event.currentTarget)
        const formData = new FormData(event.currentTarget)
        const search_text = (document.getElementById('default-search') as HTMLInputElement).value
        console.log("Search text", search_text)
        const response = await fetch('/api/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                search_text: search_text,
                num_entries: 3
            })
        })
    
        const resp = await response.json()
        console.log("Response from vector search", resp)
        // Iterate over resp.data array and generate image elements
        // using image_path field

        var filtered_images = resp.data.map( (image: CustomImage) => generateImageElement(image.image_path))
        console.log("Filtered images", filtered_images)
        setImages(
            filtered_images
        )

        } catch (error) {
            console.error(error)
        } finally {
            setIsLoading(false) // Set loading to false when the request completes
        }
    }

    async function handleFileUpload(event: any) {
        event.preventDefault()
        const file = event.target.files[0]
        console.log("File", file)
        const formData = new FormData();
        formData.append('file', file);
        console.log("Form data", formData)
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        })
        const resp = await response.json()
        console.log("Response from upload", resp)
    }

    useEffect(() => {
        fetch("/api/images")
            .then(response => response.json())
            .then(
                resp => (
                    setImages(
                        resp.data.map(generateImageElement)
                    )
                )
            )
    }, [])
    
    console.log(images)
    return (
        
        <div>
            <div class="grid-container">
                <div class="grid-item">
                    <br></br>
                    <form id="gallery-search-form" class="max-w-md mx-auto" onSubmit={onSubmit}>   
                        <label for="default-search" class="mb-2 text-sm font-medium text-gray-900 sr-only dark:text-white">Search</label>
                        <div class="relative">
                            <div class="absolute inset-y-0 start-0 flex items-center ps-3 pointer-events-none">
                                <svg class="w-4 h-4 text-gray-500 dark:text-gray-400" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 20 20">
                                    <path stroke="currentColor" stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="m19 19-4-4m0-7A7 7 0 1 1 1 8a7 7 0 0 1 14 0Z"/>
                                </svg>
                            </div>
                            <input type="text" id="default-search" class="block w-full p-4 ps-10 text-sm text-gray-900 border border-gray-300 rounded-lg bg-gray-50 focus:ring-blue-500 focus:border-blue-500 dark:bg-gray-700 dark:border-gray-600 dark:placeholder-gray-400 dark:text-white dark:focus:ring-blue-500 dark:focus:border-blue-500" placeholder="Search Mockups, Logos..." required />
                            <button type="submit" class="text-white absolute end-2.5 bottom-2.5 bg-blue-700 hover:bg-blue-800 focus:ring-4 focus:outline-none focus:ring-blue-300 font-medium rounded-lg text-sm px-4 py-2 dark:bg-blue-600 dark:hover:bg-blue-700 dark:focus:ring-blue-800">Search</button>
                        </div>
                    </form>
                </div>

                <div class="grid-item">
                    <label title="Click to upload" for="button2" class="cursor-pointer flex items-center gap-4 px-6 py-4 before:border-gray-400/60 hover:before:border-gray-300 group">
                    <div class="relative">
                        <img class="w-12" src="https://www.svgrepo.com/show/485545/upload-cicle.svg" alt="file upload icon" width="512" height="512"/>
                    </div>
                    <div class="relative">
                        <span class="block text-base font-semibold relative text-blue-900 group-hover:text-blue-500">
                            Upload an image
                        </span>
                    </div>
                    </label>
                    <input hidden="true" type="file" name="button2" id="button2" onChange={handleFileUpload}/>
                </div>
            </div>

            <br></br>
            <Gallery
                images={images}
                enableImageSelection={false}
            />
        </div>
    )
}
