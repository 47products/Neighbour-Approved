<template>
    <div class="dashboard">
      <h1>Dashboard</h1>
      <div class="dashboard-grid">
        <AppCard title="System Health" icon="pulse">
          <HealthCheck mini />
          <template #footer>
            <router-link to="/system/health">
              <AppButton variant="text">View Details</AppButton>
            </router-link>
          </template>
        </AppCard>
        
        <AppCard title="Quick Links" icon="link">
          <div class="quick-links">
            <router-link to="/system/health">
              <AppButton variant="outline">System Health</AppButton>
            </router-link>
            <!-- Add more links as your application grows -->
          </div>
        </AppCard>
        
        <AppCard title="Welcome" icon="info">
          <p>Welcome to the Neighbour Approved administrative portal. This dashboard provides access to system monitoring and management functions.</p>
        </AppCard>
      </div>
    </div>
  </template>
  
  <script>
  import AppCard from '@/components/common/AppCard.vue'
  import AppButton from '@/components/common/AppButton.vue'
  import HealthCheck from '@/components/HealthCheck.vue'
  
  export default {
    name: 'Dashboard',
    components: {
      AppCard,
      AppButton,
      HealthCheck
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .dashboard {
    h1 {
      margin-bottom: $spacing-lg;
      color: var(--color-text-primary);
    }
    
    .dashboard-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: $spacing-lg;
      
      @media (max-width: $breakpoint-md) {
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: $spacing-md;
      }
    }
    
    .quick-links {
      display: flex;
      flex-direction: column;
      gap: $spacing-sm;
    }
  }
  </style>