<template>
    <div class="dashboard-layout">
      <AppSidebar />
      <div class="content-container">
        <AppHeader />
        <main class="main-content">
          <router-view />
        </main>
      </div>
    </div>
  </template>
  
  <script>
  import AppSidebar from '@/components/AppSidebar.vue'
  import AppHeader from '@/components/AppHeader.vue'
  
  export default {
    name: 'DashboardLayout',
    components: {
      AppSidebar,
      AppHeader
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .dashboard-layout {
    display: flex;
    width: 100%;
    min-height: 100vh;
  }
  
  .content-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow-x: hidden;
  }
  
  .main-content {
    flex: 1;
    padding: $spacing-lg;
    overflow-y: auto;
    
    @media (max-width: $breakpoint-md) {
      padding: $spacing-md;
    }
    
    @media (max-width: $breakpoint-sm) {
      padding: $spacing-sm;
    }
  }
  </style>