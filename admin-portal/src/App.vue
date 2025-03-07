<template>
    <div id="app" :class="{ 'dark-theme': isDarkTheme }">
      <router-view/>
    </div>
  </template>
  
  <script>
  import { ref, onMounted, watch } from 'vue'
  
  export default {
    name: 'App',
    setup() {
      const isDarkTheme = ref(false)
  
      const checkUserPreference = () => {
        // Check system preference or localStorage setting
        const storedTheme = localStorage.getItem('theme')
        if (storedTheme) {
          isDarkTheme.value = storedTheme === 'dark'
        } else {
          isDarkTheme.value = window.matchMedia('(prefers-color-scheme: dark)').matches
        }
      }
  
      const toggleTheme = () => {
        isDarkTheme.value = !isDarkTheme.value
        localStorage.setItem('theme', isDarkTheme.value ? 'dark' : 'light')
      }
  
      // Set theme on component mount
      onMounted(() => {
        checkUserPreference()
        // Expose the toggle method to the window for global access
        window.toggleTheme = toggleTheme
      })
  
      // Watch for theme changes to update document attributes
      watch(isDarkTheme, (newValue) => {
        document.documentElement.setAttribute('data-theme', newValue ? 'dark' : 'light')
      }, { immediate: true })
  
      return {
        isDarkTheme,
        toggleTheme
      }
    }
  }
  </script>
  
  <style>
  #app {
    min-height: 100vh;
    transition: background-color 0.3s ease, color 0.3s ease;
  }
  </style>
  