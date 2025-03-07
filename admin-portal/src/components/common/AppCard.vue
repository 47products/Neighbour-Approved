<template>
    <div class="app-card" :class="{ 'has-footer': $slots.footer }">
      <div class="card-header" v-if="title || icon || $slots.header">
        <slot name="header">
          <div class="header-content">
            <span class="card-icon" v-if="icon">{{ icon }}</span>
            <h3 class="card-title" v-if="title">{{ title }}</h3>
          </div>
        </slot>
      </div>
      
      <div class="card-body">
        <slot></slot>
      </div>
      
      <div class="card-footer" v-if="$slots.footer">
        <slot name="footer"></slot>
      </div>
    </div>
  </template>
  
  <script>
  export default {
    name: 'AppCard',
    props: {
      title: {
        type: String,
        default: ''
      },
      icon: {
        type: String,
        default: ''
      }
    }
  }
  </script>
  
  <style lang="scss" scoped>
  .app-card {
    background-color: var(--color-card-bg);
    border-radius: $border-radius;
    box-shadow: var(--shadow-sm);
    overflow: hidden;
    display: flex;
    flex-direction: column;
    height: 100%;
    
    .card-header {
      padding: $spacing-md;
      border-bottom: 1px solid var(--color-border);
      
      .header-content {
        display: flex;
        align-items: center;
        
        .card-icon {
          margin-right: $spacing-sm;
          font-size: 1.25rem;
        }
        
        .card-title {
          margin: 0;
          font-size: 1.125rem;
          font-weight: 600;
          color: var(--color-text-primary);
        }
      }
    }
    
    .card-body {
      padding: $spacing-md;
      flex: 1;
    }
    
    .card-footer {
      padding: $spacing-md;
      border-top: 1px solid var(--color-border);
      background-color: var(--color-card-footer-bg);
    }
    
    &.has-footer {
      .card-body {
        padding-bottom: $spacing-sm;
      }
    }
  }
  </style>