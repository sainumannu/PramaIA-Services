/**
 * PDK Tag Management Utilities
 * 
 * Provides comprehensive tag management functionality for plugins, nodes,
 * event sources, and event types in the PramaIA PDK system.
 */

export type TagOperator = 'AND' | 'OR';

export interface TaggedItem {
  id: string;
  name: string;
  tags?: string[];
}

export interface TagFilterOptions {
  operator: TagOperator;
  caseSensitive: boolean;
  exact: boolean;
}

export interface TagStatistics {
  tag: string;
  count: number;
  percentage: number;
  items: TaggedItem[];
}

export interface TagHierarchy {
  tag: string;
  children: TagHierarchy[];
  items: TaggedItem[];
}

/**
 * Core tag management class
 */
export class TagManager {
  private items: TaggedItem[] = [];
  
  constructor(items: TaggedItem[] = []) {
    this.items = items;
  }

  /**
   * Add items to the tag manager
   */
  addItems(items: TaggedItem[]): void {
    this.items.push(...items);
  }

  /**
   * Get all unique tags from all items
   */
  getAllTags(): string[] {
    const tagSet = new Set<string>();
    this.items.forEach(item => {
      (item.tags || []).forEach(tag => tagSet.add(tag));
    });
    return Array.from(tagSet).sort();
  }

  /**
   * Filter items by tags
   */
  filterByTags(
    tags: string[], 
    options: Partial<TagFilterOptions> = {}
  ): TaggedItem[] {
    const opts = {
      operator: 'OR' as TagOperator,
      caseSensitive: false,
      exact: true,
      ...options
    };

    if (tags.length === 0) return this.items;

    return this.items.filter(item => {
      const itemTags = (item.tags || []).map(tag => 
        opts.caseSensitive ? tag : tag.toLowerCase()
      );
      
      const searchTags = tags.map(tag => 
        opts.caseSensitive ? tag : tag.toLowerCase()
      );

      const matches = searchTags.map(searchTag => {
        return itemTags.some(itemTag => {
          if (opts.exact) {
            return itemTag === searchTag;
          } else {
            return itemTag.includes(searchTag) || searchTag.includes(itemTag);
          }
        });
      });

      return opts.operator === 'AND' 
        ? matches.every(match => match)
        : matches.some(match => match);
    });
  }

  /**
   * Exclude items with specific tags
   */
  excludeTags(tags: string[]): TaggedItem[] {
    if (tags.length === 0) return this.items;

    return this.items.filter(item => {
      const itemTags = item.tags || [];
      return !tags.some(excludeTag => itemTags.includes(excludeTag));
    });
  }

  /**
   * Group items by a specific tag category
   */
  groupByTag(categoryTag: string): Record<string, TaggedItem[]> {
    const groups: Record<string, TaggedItem[]> = {};
    
    this.items.forEach(item => {
      const itemTags = item.tags || [];
      const categoryTags = itemTags.filter(tag => tag.startsWith(categoryTag));
      
      if (categoryTags.length === 0) {
        if (!groups['uncategorized']) groups['uncategorized'] = [];
        groups['uncategorized'].push(item);
      } else {
        categoryTags.forEach(tag => {
          if (!groups[tag]) groups[tag] = [];
          groups[tag].push(item);
        });
      }
    });

    return groups;
  }

  /**
   * Get tag statistics
   */
  getTagStatistics(): TagStatistics[] {
    const tagCounts: Record<string, TaggedItem[]> = {};
    
    this.items.forEach(item => {
      (item.tags || []).forEach(tag => {
        if (!tagCounts[tag]) tagCounts[tag] = [];
        tagCounts[tag].push(item);
      });
    });

    const total = this.items.length;
    
    return Object.entries(tagCounts)
      .map(([tag, items]) => ({
        tag,
        count: items.length,
        percentage: (items.length / total) * 100,
        items
      }))
      .sort((a, b) => b.count - a.count);
  }

  /**
   * Find related tags (tags that often appear together)
   */
  getRelatedTags(tag: string, minCorrelation: number = 0.1): string[] {
    const itemsWithTag = this.filterByTags([tag]);
    const totalWithTag = itemsWithTag.length;
    
    if (totalWithTag === 0) return [];

    const coOccurrences: Record<string, number> = {};
    
    itemsWithTag.forEach(item => {
      (item.tags || []).forEach(otherTag => {
        if (otherTag !== tag) {
          coOccurrences[otherTag] = (coOccurrences[otherTag] || 0) + 1;
        }
      });
    });

    return Object.entries(coOccurrences)
      .filter(([, count]) => (count / totalWithTag) >= minCorrelation)
      .sort(([, a], [, b]) => b - a)
      .map(([relatedTag]) => relatedTag);
  }

  /**
   * Build tag hierarchy based on naming conventions
   */
  buildTagHierarchy(separator: string = '-'): TagHierarchy[] {
    const hierarchy: Record<string, TagHierarchy> = {};
    
    this.getAllTags().forEach(tag => {
      const parts = tag.split(separator);
      const rootTag = parts[0];
      
      if (!hierarchy[rootTag]) {
        hierarchy[rootTag] = {
          tag: rootTag,
          children: [],
          items: []
        };
      }
      
      // Add items that have this specific tag
      const itemsWithTag = this.filterByTags([tag]);
      hierarchy[rootTag].items.push(...itemsWithTag);
      
      // Build nested structure for complex tags
      if (parts.length > 1) {
        // For now, keep flat structure but could extend for deeper nesting
        const childTag = parts.slice(1).join(separator);
        const existingChild = hierarchy[rootTag].children.find(c => c.tag === childTag);
        
        if (!existingChild) {
          hierarchy[rootTag].children.push({
            tag: childTag,
            children: [],
            items: itemsWithTag
          });
        }
      }
    });

    return Object.values(hierarchy).sort((a, b) => a.tag.localeCompare(b.tag));
  }

  /**
   * Suggest tags based on item name and description
   */
  suggestTags(name: string, description?: string): string[] {
    const suggestions = new Set<string>();
    const text = `${name} ${description || ''}`.toLowerCase();
    
    // Domain-based suggestions
    const domainMappings = {
      'pdf': ['pdf', 'document', 'file'],
      'text': ['text', 'text-processing', 'nlp'],
      'email': ['email', 'communication', 'messaging'],
      'database': ['database', 'data', 'storage'],
      'api': ['api', 'integration', 'external'],
      'schedule': ['scheduling', 'timer', 'automation'],
      'monitor': ['monitoring', 'watching', 'real-time'],
      'webhook': ['webhook', 'http', 'api'],
      'file': ['file-system', 'file', 'storage'],
      'ai': ['ai', 'machine-learning', 'intelligent'],
      'process': ['processing', 'transform', 'utility']
    };

    // Function-based suggestions
    const functionMappings = {
      'filter': ['filter', 'validation', 'clean'],
      'join': ['join', 'merge', 'combine'],
      'split': ['split', 'separate', 'parse'],
      'convert': ['convert', 'transform', 'format'],
      'analyze': ['analysis', 'examine', 'ai'],
      'send': ['output', 'communication', 'delivery'],
      'receive': ['input', 'listener', 'trigger'],
      'create': ['create', 'generate', 'build'],
      'delete': ['delete', 'remove', 'cleanup']
    };

    // Apply domain mappings
    Object.entries(domainMappings).forEach(([keyword, tags]) => {
      if (text.includes(keyword)) {
        tags.forEach(tag => suggestions.add(tag));
      }
    });

    // Apply function mappings
    Object.entries(functionMappings).forEach(([keyword, tags]) => {
      if (text.includes(keyword)) {
        tags.forEach(tag => suggestions.add(tag));
      }
    });

    // Performance indicators
    if (text.includes('fast') || text.includes('quick')) {
      suggestions.add('fast');
    }
    if (text.includes('slow') || text.includes('heavy')) {
      suggestions.add('slow');
    }

    // Maturity indicators
    if (text.includes('experimental') || text.includes('beta')) {
      suggestions.add('experimental');
    }
    if (text.includes('stable') || text.includes('production')) {
      suggestions.add('stable');
    }

    return Array.from(suggestions).sort();
  }

  /**
   * Validate tag naming conventions
   */
  validateTagName(tag: string): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    // Check format
    if (!/^[a-z0-9\-]+$/.test(tag)) {
      errors.push('Tag should only contain lowercase letters, numbers, and hyphens');
    }
    
    // Check length
    if (tag.length < 2) {
      errors.push('Tag should be at least 2 characters long');
    }
    if (tag.length > 30) {
      errors.push('Tag should be no more than 30 characters long');
    }
    
    // Check start/end
    if (tag.startsWith('-') || tag.endsWith('-')) {
      errors.push('Tag should not start or end with a hyphen');
    }
    
    // Check consecutive hyphens
    if (tag.includes('--')) {
      errors.push('Tag should not contain consecutive hyphens');
    }
    
    return {
      valid: errors.length === 0,
      errors
    };
  }

  /**
   * Get popular tags
   */
  getPopularTags(limit: number = 10): TagStatistics[] {
    return this.getTagStatistics().slice(0, limit);
  }

  /**
   * Search items by text query with tag boost
   */
  searchWithTagBoost(
    query: string, 
    tagBoost: number = 2.0
  ): Array<TaggedItem & { score: number }> {
    const normalizedQuery = query.toLowerCase();
    
    return this.items.map(item => {
      let score = 0;
      
      // Name match
      if (item.name.toLowerCase().includes(normalizedQuery)) {
        score += 10;
      }
      
      // Tag matches (with boost)
      const tagMatches = (item.tags || []).filter(tag => 
        tag.toLowerCase().includes(normalizedQuery)
      );
      score += tagMatches.length * tagBoost;
      
      // Exact tag match gets extra boost
      if ((item.tags || []).some(tag => 
        tag.toLowerCase() === normalizedQuery
      )) {
        score += 5;
      }
      
      return { ...item, score };
    })
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score);
  }
}

/**
 * Plugin-specific tag manager
 */
export class PluginTagManager extends TagManager {
  constructor(plugins: Array<{ id: string; name: string; tags?: string[] }>) {
    super(plugins);
  }

  /**
   * Get plugins by category tags
   */
  getByCategory(category: string): TaggedItem[] {
    return this.filterByTags([category]);
  }

  /**
   * Get plugins by functionality
   */
  getByFunction(func: string): TaggedItem[] {
    return this.filterByTags([func]);
  }
}

/**
 * Event Source tag manager
 */
export class EventSourceTagManager extends TagManager {
  constructor(eventSources: Array<{ id: string; name: string; tags?: string[] }>) {
    super(eventSources);
  }

  /**
   * Get event sources by lifecycle
   */
  getByLifecycle(lifecycle: string): TaggedItem[] {
    return this.filterByTags([lifecycle]);
  }
}

/**
 * Utility functions
 */
export const TagUtils = {
  /**
   * Normalize tag name
   */
  normalizeTag(tag: string): string {
    return tag
      .toLowerCase()
      .trim()
      .replace(/[^a-z0-9\-\s]/g, '')
      .replace(/\s+/g, '-')
      .replace(/--+/g, '-')
      .replace(/^-|-$/g, '');
  },

  /**
   * Generate tag from text
   */
  generateTag(text: string): string {
    return this.normalizeTag(text);
  },

  /**
   * Merge tag arrays
   */
  mergeTags(...tagArrays: (string[] | undefined)[]): string[] {
    const mergedSet = new Set<string>();
    
    tagArrays.forEach(tags => {
      (tags || []).forEach(tag => mergedSet.add(tag));
    });
    
    return Array.from(mergedSet).sort();
  },

  /**
   * Check if tags overlap
   */
  hasOverlap(tags1: string[], tags2: string[]): boolean {
    return tags1.some(tag => tags2.includes(tag));
  },

  /**
   * Calculate tag similarity
   */
  calculateSimilarity(tags1: string[], tags2: string[]): number {
    const set1 = new Set(tags1);
    const set2 = new Set(tags2);
    const intersection = new Set([...set1].filter(x => set2.has(x)));
    const union = new Set([...set1, ...set2]);
    
    return union.size === 0 ? 0 : intersection.size / union.size;
  }
};

export default TagManager;
