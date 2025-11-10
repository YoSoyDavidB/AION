import { useState } from "react";
import { Card, CardContent } from "./ui/card";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Badge } from "./ui/badge";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { Label } from "./ui/label";
import { Search, X, Filter, Calendar } from "lucide-react";

export interface SearchFilters {
  query: string;
  type?: string;
  dateFrom?: string;
  dateTo?: string;
  tags?: string[];
  sortBy?: string;
  sortOrder?: "asc" | "desc";
}

interface AdvancedSearchProps {
  onSearch: (filters: SearchFilters) => void;
  typeOptions?: { value: string; label: string }[];
  sortOptions?: { value: string; label: string }[];
  showDateFilter?: boolean;
  showTags?: boolean;
  placeholder?: string;
}

export function AdvancedSearch({
  onSearch,
  typeOptions = [],
  sortOptions = [],
  showDateFilter = true,
  showTags = true,
  placeholder = "Search...",
}: AdvancedSearchProps) {
  const [filters, setFilters] = useState<SearchFilters>({
    query: "",
    type: "all",
    sortBy: "date",
    sortOrder: "desc",
    tags: [],
  });

  const [showAdvanced, setShowAdvanced] = useState(false);
  const [tagInput, setTagInput] = useState("");

  const handleSearch = () => {
    onSearch(filters);
  };

  const handleReset = () => {
    const resetFilters: SearchFilters = {
      query: "",
      type: "all",
      sortBy: "date",
      sortOrder: "desc",
      tags: [],
    };
    setFilters(resetFilters);
    onSearch(resetFilters);
  };

  const addTag = () => {
    if (tagInput.trim() && !filters.tags?.includes(tagInput.trim())) {
      setFilters({
        ...filters,
        tags: [...(filters.tags || []), tagInput.trim()],
      });
      setTagInput("");
    }
  };

  const removeTag = (tag: string) => {
    setFilters({
      ...filters,
      tags: filters.tags?.filter((t) => t !== tag) || [],
    });
  };

  const hasActiveFilters =
    filters.query ||
    (filters.type && filters.type !== "all") ||
    filters.dateFrom ||
    filters.dateTo ||
    (filters.tags && filters.tags.length > 0);

  return (
    <div className="space-y-4">
      {/* Main Search Bar */}
      <div className="flex gap-2">
        <div className="relative flex-1">
          <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            placeholder={placeholder}
            value={filters.query}
            onChange={(e) => setFilters({ ...filters, query: e.target.value })}
            onKeyPress={(e) => e.key === "Enter" && handleSearch()}
            className="pl-9"
          />
        </div>
        <Button onClick={handleSearch}>Search</Button>
        <Button
          variant="outline"
          onClick={() => setShowAdvanced(!showAdvanced)}
        >
          <Filter className="h-4 w-4 mr-2" />
          Filters
        </Button>
        {hasActiveFilters && (
          <Button variant="ghost" onClick={handleReset}>
            <X className="h-4 w-4 mr-2" />
            Clear
          </Button>
        )}
      </div>

      {/* Advanced Filters */}
      {showAdvanced && (
        <Card>
          <CardContent className="pt-6 space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {/* Type Filter */}
              {typeOptions.length > 0 && (
                <div>
                  <Label>Type</Label>
                  <Select
                    value={filters.type}
                    onValueChange={(value) =>
                      setFilters({ ...filters, type: value })
                    }
                  >
                    <SelectTrigger className="mt-2">
                      <SelectValue placeholder="All types" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">All Types</SelectItem>
                      {typeOptions.map((option) => (
                        <SelectItem key={option.value} value={option.value}>
                          {option.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              )}

              {/* Sort By */}
              {sortOptions.length > 0 && (
                <>
                  <div>
                    <Label>Sort By</Label>
                    <Select
                      value={filters.sortBy}
                      onValueChange={(value) =>
                        setFilters({ ...filters, sortBy: value })
                      }
                    >
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        {sortOptions.map((option) => (
                          <SelectItem key={option.value} value={option.value}>
                            {option.label}
                          </SelectItem>
                        ))}
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label>Order</Label>
                    <Select
                      value={filters.sortOrder}
                      onValueChange={(value: "asc" | "desc") =>
                        setFilters({ ...filters, sortOrder: value })
                      }
                    >
                      <SelectTrigger className="mt-2">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="desc">Newest First</SelectItem>
                        <SelectItem value="asc">Oldest First</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </>
              )}

              {/* Date Range */}
              {showDateFilter && (
                <>
                  <div>
                    <Label>From Date</Label>
                    <div className="relative mt-2">
                      <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        type="date"
                        value={filters.dateFrom || ""}
                        onChange={(e) =>
                          setFilters({ ...filters, dateFrom: e.target.value })
                        }
                        className="pl-9"
                      />
                    </div>
                  </div>
                  <div>
                    <Label>To Date</Label>
                    <div className="relative mt-2">
                      <Calendar className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                      <Input
                        type="date"
                        value={filters.dateTo || ""}
                        onChange={(e) =>
                          setFilters({ ...filters, dateTo: e.target.value })
                        }
                        className="pl-9"
                      />
                    </div>
                  </div>
                </>
              )}
            </div>

            {/* Tags */}
            {showTags && (
              <div>
                <Label>Tags</Label>
                <div className="flex gap-2 mt-2">
                  <Input
                    placeholder="Add tag..."
                    value={tagInput}
                    onChange={(e) => setTagInput(e.target.value)}
                    onKeyPress={(e) => e.key === "Enter" && addTag()}
                  />
                  <Button onClick={addTag} variant="outline">
                    Add
                  </Button>
                </div>
                {filters.tags && filters.tags.length > 0 && (
                  <div className="flex flex-wrap gap-2 mt-3">
                    {filters.tags.map((tag) => (
                      <Badge key={tag} variant="secondary">
                        {tag}
                        <button
                          onClick={() => removeTag(tag)}
                          className="ml-2 hover:text-destructive"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </Badge>
                    ))}
                  </div>
                )}
              </div>
            )}
          </CardContent>
        </Card>
      )}
    </div>
  );
}
