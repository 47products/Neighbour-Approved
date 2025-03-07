<template>
    <div class="status-indicator" :class="[`status-${status}`]">
      <div class="indicator-dot"></div>
      <span class="indicator-text" v-if="showText">{{ statusText }}</span>
    </div>
  </template>
  
  <script>
  import { computed } from 'vue'
  
  export default {
    name: 'StatusIndicator',
    props: {
      status: {
        type: String,
        default: 'neutral',
        validator: (value) => ['success', 'warning', 'error', 'info', 'neutral'].includes(value)
      },
      showText: {
        type: Boolean,
        default: true
      },
      customText: {
        type: String,
        default: ''
      }
    },
    setup(props) {
      const statusText = computed(() => {
        if (props.customText) return props.customText
        
        switch (props.status) {
          case 'success': return 'Operational'
          case 'warning': return 'Degraded'
          case 'error': return 'Offline'
          case 'info': return 'Maintenance'
          default: return 'Unknown'
        }
      })
      
      return {
        statusText
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .status-indicator {
    display: inline-flex;
    align-items: center;
    gap: $spacing-xs;
    
    .indicator-dot {
      width: 12px;
      height: 12px;
      border-radius: 50%;
      background-color: var(--color-neutral);
    }
    
    .indicator-text {
      font-size: 0.875rem;
      font-weight: 500;
    }
    
    &.status-success {
      .indicator-dot {
        background-color: var(--color-success);
        box-shadow: 0 0 0 4px var(--color-success-light);
      }
      
      .indicator-text {
        color: var(--color-success);
      }
    }
    
    &.status-warning {
      .indicator-dot {
        background-color: var(--color-warning);
        box-shadow: 0 0 0 4px var(--color-warning-light);
      }
      
      .indicator-text {
        color: var(--color-warning);
      }
    }
    
    &.status-error {
      .indicator-dot {
        background-color: var(--color-error);
        box-shadow: 0 0 0 4px var(--color-error-light);
      }
      
      .indicator-text {
        color: var(--color-error);
      }
    }
    
    &.status-info {
      .indicator-dot {
        background-color: var(--color-info);
        box-shadow: 0 0 0 4px var(--color-info-light);
      }
      
      .indicator-text {
        color: var(--color-info);
      }
    }
    
    &.status-neutral {
      .indicator-dot {
        background-color: var(--color-neutral);
        box-shadow: 0 0 0 4px var(--color-neutral-light);
      }
      
      .indicator-text {
        color: var(--color-text-secondary);
      }
    }
  }
  </style>