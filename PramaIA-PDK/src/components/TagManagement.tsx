/**
 * React Components for PDK Tag Management
 * 
 * Comprehensive UI components for managing and displaying tags
 * in the PramaIA frontend interface.
 */

import React, { useState, useMemo, useCallback } from 'react';
import {
  Box,
  Button,
  Badge,
  Input,
  Select,
  Checkbox,
  VStack,
  HStack,
  Text,
  Wrap,
  WrapItem,
  IconButton,
  Popover,
  PopoverTrigger,
  PopoverContent,
  PopoverBody,
  PopoverArrow,
  Tooltip,
  useColorModeValue,
  InputGroup,
  InputLeftElement,
  Accordion,
  AccordionItem,
  AccordionButton,
  AccordionPanel,
  AccordionIcon,
  SimpleGrid,
  Stat,
  StatLabel,
  StatNumber,
  StatHelpText,
  Progress
} from '@chakra-ui/react';
import { SearchIcon, CloseIcon, InfoIcon } from '@chakra-ui/icons';
import { TagManager, TagStatistics, TagHierarchy } from '../utils/tag-manager';

// Types
export interface TaggedItem {
  id: string;
  name: string;
  tags?: string[];
  type?: string;
  description?: string;
}

export interface TagFilterProps {
  availableTags: string[];
  selectedTags: string[];
  onTagsChange: (tags: string[]) => void;
  mode?: 'AND' | 'OR';
  onModeChange?: (mode: 'AND' | 'OR') => void;
  placeholder?: string;
  maxHeight?: string;
}

export interface TagBadgeProps {
  tag: string;
  variant?: 'solid' | 'outline' | 'subtle';
  colorScheme?: string;
  size?: 'sm' | 'md' | 'lg';
  isRemovable?: boolean;
  onRemove?: (tag: string) => void;
  onClick?: (tag: string) => void;
}

export interface TagCloudProps {
  tags: TagStatistics[];
  onTagClick?: (tag: string) => void;
  maxTags?: number;
  size?: 'sm' | 'md' | 'lg';
  colorMode?: 'frequency' | 'category' | 'random';
}

export interface TagHierarchyViewProps {
  hierarchy: TagHierarchy[];
  onTagSelect?: (tag: string) => void;
  expandedItems?: string[];
  onExpandChange?: (expanded: string[]) => void;
}

/**
 * Individual tag badge component
 */
export const TagBadge: React.FC<TagBadgeProps> = ({
  tag,
  variant = 'solid',
  colorScheme,
  size = 'sm',
  isRemovable = false,
  onRemove,
  onClick
}) => {
  const handleClick = useCallback(() => {
    if (onClick) onClick(tag);
  }, [onClick, tag]);

  const handleRemove = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (onRemove) onRemove(tag);
  }, [onRemove, tag]);

  // Auto-generate color scheme based on tag
  const getColorScheme = (tag: string): string => {
    if (colorScheme) return colorScheme;
    
    const colorSchemes = ['blue', 'green', 'purple', 'red', 'orange', 'teal', 'pink'];
    const hash = tag.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
    return colorSchemes[hash % colorSchemes.length];
  };

  return (
    <Badge
      variant={variant}
      colorScheme={getColorScheme(tag)}
      size={size}
      cursor={onClick ? 'pointer' : 'default'}
      onClick={handleClick}
      display="inline-flex"
      alignItems="center"
      gap={1}
      _hover={onClick ? { opacity: 0.8 } : {}}
    >
      {tag}
      {isRemovable && (
        <IconButton
          icon={<CloseIcon />}
          size="xs"
          variant="ghost"
          onClick={handleRemove}
          aria-label={`Remove ${tag} tag`}
          minW="auto"
          h="auto"
          p={0}
        />
      )}
    </Badge>
  );
};

/**
 * Tag filter component with search and selection
 */
export const TagFilter: React.FC<TagFilterProps> = ({
  availableTags,
  selectedTags,
  onTagsChange,
  mode = 'OR',
  onModeChange,
  placeholder = "Search tags...",
  maxHeight = "300px"
}) => {
  const [searchTerm, setSearchTerm] = useState('');
  
  const filteredTags = useMemo(() => {
    if (!searchTerm) return availableTags;
    return availableTags.filter(tag => 
      tag.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [availableTags, searchTerm]);

  const handleTagToggle = useCallback((tag: string) => {
    const newTags = selectedTags.includes(tag)
      ? selectedTags.filter(t => t !== tag)
      : [...selectedTags, tag];
    onTagsChange(newTags);
  }, [selectedTags, onTagsChange]);

  const clearAllTags = useCallback(() => {
    onTagsChange([]);
  }, [onTagsChange]);

  return (
    <VStack spacing={3} align="stretch">
      {/* Search Input */}
      <InputGroup>
        <InputLeftElement>
          <SearchIcon color="gray.400" />
        </InputLeftElement>
        <Input
          placeholder={placeholder}
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
        />
      </InputGroup>

      {/* Mode Selector and Clear Button */}
      <HStack justify="space-between">
        {onModeChange && (
          <Select
            value={mode}
            onChange={(e) => onModeChange(e.target.value as 'AND' | 'OR')}
            width="auto"
            size="sm"
          >
            <option value="OR">Any tag (OR)</option>
            <option value="AND">All tags (AND)</option>
          </Select>
        )}
        
        {selectedTags.length > 0 && (
          <Button size="sm" variant="ghost" onClick={clearAllTags}>
            Clear All
          </Button>
        )}
      </HStack>

      {/* Selected Tags */}
      {selectedTags.length > 0 && (
        <Box>
          <Text fontSize="sm" fontWeight="semibold" mb={2}>
            Selected ({selectedTags.length}):
          </Text>
          <Wrap>
            {selectedTags.map(tag => (
              <WrapItem key={tag}>
                <TagBadge
                  tag={tag}
                  isRemovable
                  onRemove={handleTagToggle}
                />
              </WrapItem>
            ))}
          </Wrap>
        </Box>
      )}

      {/* Available Tags */}
      <Box maxHeight={maxHeight} overflowY="auto">
        <Text fontSize="sm" fontWeight="semibold" mb={2}>
          Available Tags ({filteredTags.length}):
        </Text>
        <VStack align="stretch" spacing={1}>
          {filteredTags.map(tag => (
            <Checkbox
              key={tag}
              isChecked={selectedTags.includes(tag)}
              onChange={() => handleTagToggle(tag)}
              size="sm"
            >
              <TagBadge tag={tag} />
            </Checkbox>
          ))}
        </VStack>
      </Box>
    </VStack>
  );
};

/**
 * Tag cloud visualization
 */
export const TagCloud: React.FC<TagCloudProps> = ({
  tags,
  onTagClick,
  maxTags = 50,
  size = 'md',
  colorMode = 'frequency'
}) => {
  const displayTags = useMemo(() => {
    return tags.slice(0, maxTags);
  }, [tags, maxTags]);

  const getTagSize = useCallback((tag: TagStatistics) => {
    const maxCount = Math.max(...tags.map(t => t.count));
    const minCount = Math.min(...tags.map(t => t.count));
    const ratio = (tag.count - minCount) / (maxCount - minCount);
    
    const sizeMap = {
      sm: { min: 'xs', max: 'md' },
      md: { min: 'sm', max: 'lg' },
      lg: { min: 'md', max: 'xl' }
    };
    
    const sizes = ['xs', 'sm', 'md', 'lg', 'xl'];
    const currentSizes = sizeMap[size];
    const minIndex = sizes.indexOf(currentSizes.min);
    const maxIndex = sizes.indexOf(currentSizes.max);
    
    const targetIndex = Math.round(minIndex + (maxIndex - minIndex) * ratio);
    return sizes[targetIndex];
  }, [tags, size]);

  const getColorScheme = useCallback((tag: TagStatistics, index: number) => {
    switch (colorMode) {
      case 'frequency':
        const colors = ['red', 'orange', 'yellow', 'green', 'blue', 'purple'];
        const maxCount = Math.max(...tags.map(t => t.count));
        const ratio = tag.count / maxCount;
        return colors[Math.floor(ratio * (colors.length - 1))];
      
      case 'category':
        const categoryColors = ['blue', 'green', 'purple', 'red', 'orange', 'teal'];
        return categoryColors[index % categoryColors.length];
      
      case 'random':
      default:
        const randomColors = ['blue', 'green', 'purple', 'red', 'orange', 'teal', 'pink', 'cyan'];
        const hash = tag.tag.split('').reduce((acc, char) => char.charCodeAt(0) + acc, 0);
        return randomColors[hash % randomColors.length];
    }
  }, [colorMode, tags]);

  return (
    <Wrap spacing={2} justify="center">
      {displayTags.map((tag, index) => (
        <WrapItem key={tag.tag}>
          <Tooltip label={`${tag.count} items (${tag.percentage.toFixed(1)}%)`}>
            <Box>
              <TagBadge
                tag={tag.tag}
                size={getTagSize(tag) as any}
                colorScheme={getColorScheme(tag, index)}
                onClick={onTagClick}
              />
            </Box>
          </Tooltip>
        </WrapItem>
      ))}
    </Wrap>
  );
};

/**
 * Tag hierarchy tree view
 */
export const TagHierarchyView: React.FC<TagHierarchyViewProps> = ({
  hierarchy,
  onTagSelect,
  expandedItems = [],
  onExpandChange
}) => {
  const handleExpand = useCallback((tag: string) => {
    const newExpanded = expandedItems.includes(tag)
      ? expandedItems.filter(item => item !== tag)
      : [...expandedItems, tag];
    
    if (onExpandChange) onExpandChange(newExpanded);
  }, [expandedItems, onExpandChange]);

  const renderHierarchyItem = (item: TagHierarchy, level: number = 0) => (
    <AccordionItem key={item.tag} border="none">
      <AccordionButton
        pl={level * 4}
        onClick={() => handleExpand(item.tag)}
        _hover={{ bg: 'gray.50' }}
      >
        <Box flex="1" textAlign="left">
          <HStack>
            <TagBadge 
              tag={item.tag} 
              onClick={onTagSelect}
            />
            <Text fontSize="sm" color="gray.500">
              ({item.items.length})
            </Text>
          </HStack>
        </Box>
        {item.children.length > 0 && <AccordionIcon />}
      </AccordionButton>
      
      {item.children.length > 0 && (
        <AccordionPanel pb={2}>
          <Accordion allowMultiple>
            {item.children.map(child => renderHierarchyItem(child, level + 1))}
          </Accordion>
        </AccordionPanel>
      )}
    </AccordionItem>
  );

  return (
    <Accordion allowMultiple>
      {hierarchy.map(item => renderHierarchyItem(item))}
    </Accordion>
  );
};

/**
 * Tag statistics dashboard
 */
export const TagStatsDashboard: React.FC<{ stats: TagStatistics[] }> = ({ stats }) => {
  const totalItems = useMemo(() => {
    return stats.reduce((sum, stat) => sum + stat.count, 0);
  }, [stats]);

  const topTags = useMemo(() => stats.slice(0, 10), [stats]);

  return (
    <VStack spacing={6} align="stretch">
      <SimpleGrid columns={{ base: 1, md: 3 }} spacing={4}>
        <Stat>
          <StatLabel>Total Tags</StatLabel>
          <StatNumber>{stats.length}</StatNumber>
          <StatHelpText>Unique tags in system</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Total Items</StatLabel>
          <StatNumber>{totalItems}</StatNumber>
          <StatHelpText>Items with tags</StatHelpText>
        </Stat>
        
        <Stat>
          <StatLabel>Avg Tags/Item</StatLabel>
          <StatNumber>{(stats.length / Math.max(totalItems, 1)).toFixed(1)}</StatNumber>
          <StatHelpText>Tag density</StatHelpText>
        </Stat>
      </SimpleGrid>

      <Box>
        <Text fontSize="lg" fontWeight="semibold" mb={4}>
          Top Tags
        </Text>
        <VStack spacing={3} align="stretch">
          {topTags.map((stat, index) => (
            <Box key={stat.tag}>
              <HStack justify="space-between" mb={1}>
                <HStack>
                  <Text fontWeight="medium">#{index + 1}</Text>
                  <TagBadge tag={stat.tag} />
                </HStack>
                <Text fontSize="sm" color="gray.500">
                  {stat.count} ({stat.percentage.toFixed(1)}%)
                </Text>
              </HStack>
              <Progress 
                value={stat.percentage} 
                colorScheme="blue" 
                size="sm" 
                bg="gray.100"
              />
            </Box>
          ))}
        </VStack>
      </Box>
    </VStack>
  );
};

/**
 * Comprehensive tag management panel
 */
export interface TagManagementPanelProps {
  items: TaggedItem[];
  onItemsFilter: (filteredItems: TaggedItem[]) => void;
  showStats?: boolean;
  showHierarchy?: boolean;
  showCloud?: boolean;
}

export const TagManagementPanel: React.FC<TagManagementPanelProps> = ({
  items,
  onItemsFilter,
  showStats = true,
  showHierarchy = true,
  showCloud = true
}) => {
  const [selectedTags, setSelectedTags] = useState<string[]>([]);
  const [filterMode, setFilterMode] = useState<'AND' | 'OR'>('OR');
  
  const tagManager = useMemo(() => new TagManager(items), [items]);
  
  const availableTags = useMemo(() => tagManager.getAllTags(), [tagManager]);
  const tagStats = useMemo(() => tagManager.getTagStatistics(), [tagManager]);
  const tagHierarchy = useMemo(() => tagManager.buildTagHierarchy(), [tagManager]);
  
  const filteredItems = useMemo(() => {
    if (selectedTags.length === 0) return items;
    return tagManager.filterByTags(selectedTags, { operator: filterMode });
  }, [tagManager, selectedTags, filterMode, items]);

  // Update parent when filtered items change
  React.useEffect(() => {
    onItemsFilter(filteredItems);
  }, [filteredItems, onItemsFilter]);

  const bgColor = useColorModeValue('white', 'gray.800');
  const borderColor = useColorModeValue('gray.200', 'gray.700');

  return (
    <Box bg={bgColor} borderWidth={1} borderColor={borderColor} borderRadius="md" p={4}>
      <VStack spacing={6} align="stretch">
        <Box>
          <Text fontSize="lg" fontWeight="semibold" mb={4}>
            Tag Filter
          </Text>
          <TagFilter
            availableTags={availableTags}
            selectedTags={selectedTags}
            onTagsChange={setSelectedTags}
            mode={filterMode}
            onModeChange={setFilterMode}
          />
        </Box>

        {showCloud && tagStats.length > 0 && (
          <Box>
            <Text fontSize="lg" fontWeight="semibold" mb={4}>
              Tag Cloud
            </Text>
            <TagCloud
              tags={tagStats}
              onTagClick={(tag) => {
                if (!selectedTags.includes(tag)) {
                  setSelectedTags([...selectedTags, tag]);
                }
              }}
            />
          </Box>
        )}

        {showStats && (
          <Box>
            <Text fontSize="lg" fontWeight="semibold" mb={4}>
              Statistics
            </Text>
            <TagStatsDashboard stats={tagStats} />
          </Box>
        )}

        {showHierarchy && tagHierarchy.length > 0 && (
          <Box>
            <Text fontSize="lg" fontWeight="semibold" mb={4}>
              Tag Hierarchy
            </Text>
            <TagHierarchyView
              hierarchy={tagHierarchy}
              onTagSelect={(tag) => {
                if (!selectedTags.includes(tag)) {
                  setSelectedTags([...selectedTags, tag]);
                }
              }}
            />
          </Box>
        )}
      </VStack>
    </Box>
  );
};

export default TagManagementPanel;
