<template>
    <header class="app-header">
      <div class="header-content">
        <div class="header-left">
          <button 
            class="mobile-menu-toggle" 
            @click="toggleSidebar"
            aria-label="Toggle menu"
          >
            <span></span>
            <span></span>
            <span></span>
          </button>
          <h1 class="page-title">{{ currentPageTitle }}</h1>
        </div>
        
        <div class="header-right">
          <button 
            class="theme-toggle" 
            @click="toggleTheme" 
            :title="isDarkTheme ? 'Switch to light theme' : 'Switch to dark theme'"
          >
            <span class="icon" v-if="isDarkTheme">☀️</span>
            <span class="icon" v-else>🌙</span>
          </button>
          
          <!-- Profile dropdown could go here in the future -->
        </div>
      </div>
    </header>
  </template>
  
  <script>
  import { computed } from 'vue'
  import { useRoute } from 'vue-router'
  
  export default {
    name: 'AppHeader',
    setup() {
      const route = useRoute()
      
      const currentPageTitle = computed(() => {
        return route.meta.title || 'Dashboard'
      })
      
      const isDarkTheme = computed(() => {
        return document.documentElement.getAttribute('data-theme') === 'dark'
      })
      
      const toggleTheme = () => {
        window.toggleTheme()
      }
      
      const toggleSidebar = () => {
        document.body.classList.toggle('sidebar-open')
      }
      
      return {
        currentPageTitle,
        isDarkTheme,
        toggleTheme,
        toggleSidebar
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .app-header {
    height: 64px;
    background-color: var(--color-header-bg);
    box-shadow: var(--shadow-sm);
    position: sticky;
    top: 0;
    z-index: 10;
    
    .header-content {
      display: flex;
      justify-content: space-between;
      align-items: center;
      height: 100%;
      padding: 0 $spacing-lg;
      
      @media (max-width: $breakpoint-md) {
        padding: 0 $spacing-md;
      }
    }
    
    .header-left {
      display: flex;
      align-items: center;
      
      .mobile-menu-toggle {
        display: none;
        flex-direction: column;
        justify-content: space-between;
        width: 24px;
        height: 18px;
        background: transparent;
        border: none;
        cursor: pointer;
        padding: 0;
        margin-right: $spacing-md;
        
        span {
          display: block;
          height: 2px;
          width: 100%;
          background-color: var(--color-text-primary);
          transition: transform 0.3s ease;
        }
        
        @media (max-width: $breakpoint-md) {
          display: flex;
        }
      }
      
      .page-title {
        margin: 0;
        font-size: 1.25rem;
        font-weight: 600;
        color: var(--color-text-primary);
      }
    }
    
    .header-right {
      display: flex;
      align-items: center;
      
      .theme-toggle {
        background: transparent;
        border: none;
        cursor: pointer;
        font-size: 1.25rem;
        padding: $spacing-sm;
        border-radius: $border-radius-sm;
        transition: background-color 0.2s ease;
        
        &:hover {
          background-color: var(--color-bg-hover);
        }
        
        .icon {
          display: inline-block;
        }
      }
    }
  }
  </style>