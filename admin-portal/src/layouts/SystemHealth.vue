<template>
    <div class="system-health">
      <h1>System Health</h1>
      
      <div class="health-card">
        <h2>Health Check Status</h2>
        <p class="description">
          Check the current status of the Neighbour Approved API by performing a health check. 
          This verifies that the system's core components are operational.
        </p>
        
        <HealthCheck />
      </div>
      
      <div class="health-sections">
        <AppCard title="Response Information" icon="info">
          <template v-if="healthData">
            <div class="health-info">
              <div class="info-item">
                <strong>Status:</strong>
                <span>{{ healthData.status }}</span>
              </div>
              <div class="info-item">
                <strong>Version:</strong>
                <span>{{ healthData.version }}</span>
              </div>
              <div class="info-item">
                <strong>Last Check:</strong>
                <span>{{ lastChecked }}</span>
              </div>
            </div>
          </template>
          <template v-else>
            <p>No health data available. Run a health check to see system status.</p>
          </template>
        </AppCard>
        
        <AppCard title="About Health Checks" icon="help">
          <p>The health check endpoint verifies that the API is operating correctly and can process requests. 
             It serves as a simple indicator of system availability.</p>
          <p>Regular health checks can help detect issues before they cause service disruptions.</p>
        </AppCard>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, computed } from 'vue'
  import HealthCheck from '@/components/HealthCheck.vue'
  import AppCard from '@/components/common/AppCard.vue'
  
  export default {
    name: 'SystemHealth',
    components: {
      HealthCheck,
      AppCard
    },
    setup() {
      const healthData = ref(null)
      const lastCheckedTime = ref(null)
      
      const lastChecked = computed(() => {
        if (!lastCheckedTime.value) return 'Not checked yet'
        return new Date(lastCheckedTime.value).toLocaleString()
      })
      
      // Method that can be called by the HealthCheck component to update data
      const updateHealthData = (data) => {
        healthData.value = data
        lastCheckedTime.value = new Date()
      }
      
      return {
        healthData,
        lastChecked,
        updateHealthData
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .system-health {
    h1 {
      margin-bottom: $spacing-lg;
      color: var(--color-text-primary);
    }
    
    .health-card {
      background-color: var(--color-card-bg);
      border-radius: $border-radius;
      padding: $spacing-lg;
      margin-bottom: $spacing-lg;
      box-shadow: var(--shadow-sm);
      
      h2 {
        margin-top: 0;
        margin-bottom: $spacing-md;
        color: var(--color-text-primary);
      }
      
      .description {
        margin-bottom: $spacing-lg;
        color: var(--color-text-secondary);
      }
    }
    
    .health-sections {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
      gap: $spacing-lg;
      
      @media (max-width: $breakpoint-md) {
        grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
        gap: $spacing-md;
      }
    }
    
    .health-info {
      .info-item {
        display: flex;
        justify-content: space-between;
        padding: $spacing-sm 0;
        border-bottom: 1px solid var(--color-border);
        
        &:last-child {
          border-bottom: none;
        }
        
        strong {
          color: var(--color-text-primary);
        }
        
        span {
          color: var(--color-text-secondary);
        }
      }
    }
  }
  </style>