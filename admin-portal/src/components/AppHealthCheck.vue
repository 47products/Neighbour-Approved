<template>
    <div class="health-check" :class="{ 'mini': mini }">
      <div class="health-status" v-if="healthData">
        <StatusIndicator :status="healthData.status === 'ok' ? 'success' : 'error'" />
        <div class="health-details" v-if="!mini">
          <p class="status-text">
            System is {{ healthData.status === 'ok' ? 'operational' : 'experiencing issues' }}
          </p>
          <p class="version-text">
            API Version: {{ healthData.version }}
          </p>
        </div>
      </div>
      
      <div class="health-check-actions">
        <AppButton 
          @click="checkHealth" 
          :loading="loading"
          :variant="mini ? 'outline' : 'primary'"
          :class="{ 'btn-mini': mini }"
        >
          {{ mini ? 'Check' : 'Run Health Check' }}
        </AppButton>
      </div>
      
      <div class="health-message" v-if="message && !mini">
        <p :class="['message', messageType]">{{ message }}</p>
      </div>
    </div>
  </template>
  
  <script>
  import { ref, onMounted } from 'vue'
  import axios from 'axios'
  import AppButton from '@/components/common/AppButton.vue'
  import StatusIndicator from '@/components/common/StatusIndicator.vue'
  
  export default {
    name: 'HealthCheck',
    components: {
      AppButton,
      StatusIndicator
    },
    props: {
      mini: {
        type: Boolean,
        default: false
      },
      autoCheck: {
        type: Boolean,
        default: false
      }
    },
    emits: ['health-data-updated'],
    setup(props, { emit }) {
      const healthData = ref(null)
      const loading = ref(false)
      const message = ref('')
      const messageType = ref('info')
      
      const checkHealth = async () => {
        loading.value = true
        message.value = ''
        
        try {
          const apiUrl = `${import.meta.env.VITE_API_BASE_URL}/system/health/health_check`
          const response = await axios.get(apiUrl)
          
          healthData.value = response.data
          
          if (response.data.status === 'ok') {
            message.value = '✅ Health check successful. All systems operational.'
            messageType.value = 'success'
          } else {
            message.value = '⚠️ System may be experiencing issues.'
            messageType.value = 'warning'
          }
          
          // Emit the health data to parent components
          emit('health-data-updated', response.data)
        } catch (error) {
          console.error('Health check failed:', error)
          healthData.value = { status: 'error', version: 'unknown' }
          message.value = '❌ Health check failed. Unable to connect to the API.'
          messageType.value = 'error'
        } finally {
          loading.value = false
        }
      }
      
      onMounted(() => {
        if (props.autoCheck) {
          checkHealth()
        }
      })
      
      return {
        healthData,
        loading,
        message,
        messageType,
        checkHealth
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .health-check {
    display: flex;
    flex-direction: column;
    gap: $spacing-md;
    
    &.mini {
      flex-direction: row;
      align-items: center;
      justify-content: space-between;
      gap: $spacing-sm;
    }
    
    .health-status {
      display: flex;
      align-items: center;
      gap: $spacing-md;
      
      .health-details {
        .status-text {
          margin: 0;
          font-weight: 500;
          color: var(--color-text-primary);
        }
        
        .version-text {
          margin: $spacing-xs 0 0;
          font-size: 0.875rem;
          color: var(--color-text-secondary);
        }
      }
    }
    
    .health-check-actions {
      .btn-mini {
        padding: $spacing-xs $spacing-sm;
        font-size: 0.875rem;
      }
    }
    
    .health-message {
      .message {
        padding: $spacing-sm;
        border-radius: $border-radius-sm;
        font-size: 0.875rem;
        
        &.success {
          background-color: var(--color-success-light);
          color: var(--color-success);
        }
        
        &.warning {
          background-color: var(--color-warning-light);
          color: var(--color-warning);
        }
        
        &.error {
          background-color: var(--color-error-light);
          color: var(--color-error);
        }
        
        &.info {
          background-color: var(--color-info-light);
          color: var(--color-info);
        }
      }
    }
  }
  </style>