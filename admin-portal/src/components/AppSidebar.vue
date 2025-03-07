<template>
    <aside class="app-sidebar" :class="{ 'collapsed': isCollapsed }">
      <div class="sidebar-header">
        <div class="logo-container">
          <img src="@/assets/logo.svg" alt="Neighbour Approved" class="logo" />
          <span class="app-name" v-if="!isCollapsed">Neighbour Approved</span>
        </div>
        <button 
          class="collapse-toggle" 
          @click="toggleCollapse"
          :title="isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'"
        >
          <span class="toggle-icon">{{ isCollapsed ? '→' : '←' }}</span>
        </button>
      </div>
      
      <nav class="sidebar-nav">
        <ul class="nav-list">
          <li v-for="item in navItems" :key="item.path">
            <router-link 
              :to="item.path" 
              class="nav-link" 
              :class="{ 'active': isActive(item.path) }"
            >
              <span class="nav-icon">{{ item.icon }}</span>
              <span class="nav-text" v-if="!isCollapsed">{{ item.title }}</span>
            </router-link>
          </li>
        </ul>
      </nav>
      
      <div class="sidebar-footer">
        <div class="version" v-if="!isCollapsed">v{{ version }}</div>
      </div>
    </aside>
  </template>
  
  <script>
  import { ref, computed } from 'vue'
  import { useRoute } from 'vue-router'
  
  export default {
    name: 'AppSidebar',
    setup() {
      const route = useRoute()
      const isCollapsed = ref(false)
      const version = ref(import.meta.env.VITE_APP_VERSION || '0.1.0')
      
      const navItems = [
        { path: '/', title: 'Dashboard', icon: '📊' },
        { path: '/system/health', title: 'System Health', icon: '🔍' }
      ]
      
      const toggleCollapse = () => {
        isCollapsed.value = !isCollapsed.value
        localStorage.setItem('sidebarCollapsed', isCollapsed.value ? 'true' : 'false')
      }
      
      const isActive = (path) => {
        // Exact match for home path
        if (path === '/') {
          return route.path === path
        }
        // For other paths, check if current route starts with the path
        return route.path.startsWith(path)
      }
      
      return {
        isCollapsed,
        navItems,
        version,
        toggleCollapse,
        isActive
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .app-sidebar {
    width: 250px;
    background-color: var(--color-sidebar-bg);
    border-right: 1px solid var(--color-border);
    display: flex;
    flex-direction: column;
    transition: width 0.3s ease;
    overflow: hidden;
    position: relative;
    
    &.collapsed {
      width: 64px;
    }
    
    @media (max-width: $breakpoint-md) {
      position: fixed;
      top: 0;
      left: 0;
      height: 100vh;
      z-index: 20;
      transform: translateX(-100%);
      transition: transform 0.3s ease;
      box-shadow: var(--shadow-lg);
      
      .sidebar-open & {
        transform: translateX(0);
      }
    }
    
    .sidebar-header {
      height: 64px;
      display: flex;
      align-items: center;
      padding: 0 $spacing-md;
      border-bottom: 1px solid var(--color-border);
      
      .logo-container {
        display: flex;
        align-items: center;
        flex: 1;
        overflow: hidden;
        
        .logo {
          width: 32px;
          height: 32px;
          margin-right: $spacing-sm;
        }
        
        .app-name {
          font-weight: 600;
          font-size: 1rem;
          color: var(--color-text-primary);
          white-space: nowrap;
        }
      }
      
      .collapse-toggle {
        background: transparent;
        border: none;
        cursor: pointer;
        width: 24px;
        height: 24px;
        display: flex;
        align-items: center;
        justify-content: center;
        color: var(--color-text-secondary);
        
        @media (max-width: $breakpoint-md) {
          display: none;
        }
      }
    }
    
    .sidebar-nav {
      flex: 1;
      padding: $spacing-md 0;
      overflow-y: auto;
      
      .nav-list {
        list-style: none;
        margin: 0;
        padding: 0;
        
        .nav-link {
          display: flex;
          align-items: center;
          padding: $spacing-sm $spacing-md;
          color: var(--color-text-secondary);
          text-decoration: none;
          transition: all 0.2s ease;
          
          &:hover {
            background-color: var(--color-bg-hover);
            color: var(--color-text-primary);
          }
          
          &.active {
            background-color: var(--color-primary-light);
            color: var(--color-primary);
            font-weight: 500;
          }
          
          .nav-icon {
            font-size: 1.25rem;
            width: 24px;
            text-align: center;
            margin-right: $spacing-md;
          }
          
          .nav-text {
            white-space: nowrap;
          }
        }
      }
    }
    
    .sidebar-footer {
      padding: $spacing-sm $spacing-md;
      border-top: 1px solid var(--color-border);
      font-size: 0.75rem;
      color: var(--color-text-secondary);
      text-align: center;
    }
  }
  </style>