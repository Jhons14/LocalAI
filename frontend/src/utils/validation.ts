import DOMPurify from 'dompurify';

// Input validation rules
export const ValidationRules = {
  message: {
    maxLength: 4000,
    minLength: 1,
    required: true,
  },
  apiKey: {
    minLength: 20,
    maxLength: 200,
    required: true,
    pattern: /^sk-[a-zA-Z0-9]{20,}$/, // OpenAI API key pattern
  },
  threadId: {
    pattern: /^[a-zA-Z0-9-_]{8,50}$/,
    required: false,
  },
  modelName: {
    maxLength: 100,
    minLength: 1,
    required: true,
    pattern: /^[a-zA-Z0-9.:_-]+$/,
  },
} as const;

export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  sanitizedValue?: string;
}

export class InputValidator {
  static validateMessage(input: string): ValidationResult {
    const errors: string[] = [];
    
    if (!input || input.trim().length === 0) {
      if (ValidationRules.message.required) {
        errors.push('Message is required');
      }
      return { isValid: false, errors };
    }

    const trimmed = input.trim();
    
    if (trimmed.length < ValidationRules.message.minLength) {
      errors.push(`Message must be at least ${ValidationRules.message.minLength} character long`);
    }
    
    if (trimmed.length > ValidationRules.message.maxLength) {
      errors.push(`Message must not exceed ${ValidationRules.message.maxLength} characters`);
    }

    // Check for potential XSS attempts
    const sanitized = this.sanitizeInput(trimmed);
    if (sanitized !== trimmed) {
      errors.push('Message contains potentially unsafe content');
    }

    // Check for suspicious patterns
    if (this.containsSuspiciousPatterns(trimmed)) {
      errors.push('Message contains suspicious patterns');
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue: sanitized,
    };
  }

  static validateApiKey(input: string): ValidationResult {
    const errors: string[] = [];
    
    if (!input || input.trim().length === 0) {
      if (ValidationRules.apiKey.required) {
        errors.push('API key is required');
      }
      return { isValid: false, errors };
    }

    const trimmed = input.trim();
    
    if (trimmed.length < ValidationRules.apiKey.minLength) {
      errors.push(`API key must be at least ${ValidationRules.apiKey.minLength} characters long`);
    }
    
    if (trimmed.length > ValidationRules.apiKey.maxLength) {
      errors.push(`API key must not exceed ${ValidationRules.apiKey.maxLength} characters`);
    }

    if (!ValidationRules.apiKey.pattern.test(trimmed)) {
      errors.push('Invalid API key format');
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue: trimmed,
    };
  }

  static validateThreadId(input: string): ValidationResult {
    const errors: string[] = [];
    
    if (!input || input.trim().length === 0) {
      return { isValid: true, errors }; // Thread ID is optional
    }

    const trimmed = input.trim();
    
    if (!ValidationRules.threadId.pattern.test(trimmed)) {
      errors.push('Invalid thread ID format');
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue: trimmed,
    };
  }

  static validateModelName(input: string): ValidationResult {
    const errors: string[] = [];
    
    if (!input || input.trim().length === 0) {
      if (ValidationRules.modelName.required) {
        errors.push('Model name is required');
      }
      return { isValid: false, errors };
    }

    const trimmed = input.trim();
    
    if (trimmed.length < ValidationRules.modelName.minLength) {
      errors.push(`Model name must be at least ${ValidationRules.modelName.minLength} character long`);
    }
    
    if (trimmed.length > ValidationRules.modelName.maxLength) {
      errors.push(`Model name must not exceed ${ValidationRules.modelName.maxLength} characters`);
    }

    if (!ValidationRules.modelName.pattern.test(trimmed)) {
      errors.push('Model name contains invalid characters');
    }

    return {
      isValid: errors.length === 0,
      errors,
      sanitizedValue: trimmed,
    };
  }

  // Sanitize input to prevent XSS
  static sanitizeInput(input: string): string {
    // Remove any HTML tags and dangerous characters
    const sanitized = DOMPurify.sanitize(input, { 
      ALLOWED_TAGS: [],
      ALLOWED_ATTR: [],
    });
    
    // Additional sanitization for specific characters
    return sanitized
      .replace(/<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>/gi, '') // Remove script tags
      .replace(/javascript:/gi, '') // Remove javascript: protocol
      .replace(/on\w+\s*=/gi, '') // Remove event handlers
      .trim();
  }

  // Check for suspicious patterns that might indicate malicious input
  private static containsSuspiciousPatterns(input: string): boolean {
    const suspiciousPatterns = [
      /<script/i,
      /javascript:/i,
      /vbscript:/i,
      /on\w+\s*=/i,
      /eval\s*\(/i,
      /expression\s*\(/i,
      /url\s*\(/i,
      /import\s*\(/i,
    ];

    return suspiciousPatterns.some(pattern => pattern.test(input));
  }

  // Validate multiple fields at once
  static validateForm(data: Record<string, string>): Record<string, ValidationResult> {
    const results: Record<string, ValidationResult> = {};

    Object.entries(data).forEach(([key, value]) => {
      switch (key) {
        case 'message':
          results[key] = this.validateMessage(value);
          break;
        case 'apiKey':
          results[key] = this.validateApiKey(value);
          break;
        case 'threadId':
          results[key] = this.validateThreadId(value);
          break;
        case 'modelName':
          results[key] = this.validateModelName(value);
          break;
        default:
          // Generic validation for unknown fields
          results[key] = {
            isValid: true,
            errors: [],
            sanitizedValue: this.sanitizeInput(value),
          };
      }
    });

    return results;
  }
}