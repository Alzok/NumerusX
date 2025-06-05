import React, { useMemo } from 'react';
import {
  useReactTable,
  getCoreRowModel,
  getPaginationRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  ColumnDef,
  flexRender,
  SortingState,
  ColumnFiltersState,
} from '@tanstack/react-table';
import { TradeEntry } from '@/lib/apiClient';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { ChevronUp, ChevronDown, ArrowUpDown } from 'lucide-react';

interface TradesTableProps {
  data: TradeEntry[];
  isLoading?: boolean;
  onLoadMore?: () => void;
  hasMore?: boolean;
}

export const TradesTable: React.FC<TradesTableProps> = ({
  data,
  isLoading = false,
  onLoadMore,
  hasMore = false,
}) => {
  const [sorting, setSorting] = React.useState<SortingState>([]);
  const [columnFilters, setColumnFilters] = React.useState<ColumnFiltersState>([]);
  const [globalFilter, setGlobalFilter] = React.useState('');

  const columns = useMemo<ColumnDef<TradeEntry>[]>(
    () => [
      {
        accessorKey: 'timestamp_utc',
        header: 'Date',
        cell: ({ row }) => {
          const date = new Date(row.getValue('timestamp_utc'));
          return date.toLocaleString('fr-FR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
          });
        },
      },
      {
        accessorKey: 'pair',
        header: 'Paire',
        cell: ({ row }) => (
          <span className="font-medium">{row.getValue('pair')}</span>
        ),
      },
      {
        accessorKey: 'type',
        header: 'Type',
        cell: ({ row }) => {
          const type = row.getValue('type') as string;
          return (
            <Badge 
              variant={type === 'BUY' ? 'default' : 'destructive'}
              className={type === 'BUY' ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'}
            >
              {type}
            </Badge>
          );
        },
      },
      {
        accessorKey: 'amount_tokens',
        header: 'Quantité',
        cell: ({ row }) => {
          const amount = parseFloat(row.getValue('amount_tokens'));
          return amount.toLocaleString('fr-FR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 6,
          });
        },
      },
      {
        accessorKey: 'price_usd',
        header: 'Prix (USD)',
        cell: ({ row }) => {
          const price = parseFloat(row.getValue('price_usd'));
          return `$${price.toLocaleString('fr-FR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 6,
          })}`;
        },
      },
      {
        accessorKey: 'status',
        header: 'Statut',
        cell: ({ row }) => {
          const status = row.getValue('status') as string;
          const statusColor = {
            'COMPLETED': 'bg-green-100 text-green-800',
            'PENDING': 'bg-yellow-100 text-yellow-800',
            'FAILED': 'bg-red-100 text-red-800',
          }[status] || 'bg-gray-100 text-gray-800';
          
          return (
            <Badge className={statusColor}>
              {status}
            </Badge>
          );
        },
      },
      {
        accessorKey: 'reason_source',
        header: 'Source',
        cell: ({ row }) => (
          <span className="text-sm text-muted-foreground">
            {row.getValue('reason_source')}
          </span>
        ),
      },
    ],
    []
  );

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    onSortingChange: setSorting,
    onColumnFiltersChange: setColumnFilters,
    onGlobalFilterChange: setGlobalFilter,
    state: {
      sorting,
      columnFilters,
      globalFilter,
    },
    initialState: {
      pagination: {
        pageSize: 10,
      },
    },
  });

  return (
    <div className="space-y-4">
      {/* Filtres */}
      <div className="flex items-center space-x-2">
        <Input
          placeholder="Rechercher dans les trades..."
          value={globalFilter ?? ''}
          onChange={(event: React.ChangeEvent<HTMLInputElement>) => setGlobalFilter(String(event.target.value))}
          className="max-w-sm"
        />
      </div>

      {/* Table */}
      <div className="rounded-md border">
        <Table>
          <TableHeader>
            {table.getHeaderGroups().map((headerGroup) => (
              <TableRow key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <TableHead key={header.id}>
                    {header.isPlaceholder ? null : (
                      <div
                        className={
                          header.column.getCanSort()
                            ? 'cursor-pointer select-none flex items-center space-x-1'
                            : ''
                        }
                        onClick={header.column.getToggleSortingHandler()}
                      >
                        {flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                        {header.column.getCanSort() && (
                          <span className="text-xs">
                            {{
                              asc: <ChevronUp className="h-4 w-4" />,
                              desc: <ChevronDown className="h-4 w-4" />,
                            }[header.column.getIsSorted() as string] ?? (
                              <ArrowUpDown className="h-4 w-4 opacity-50" />
                            )}
                          </span>
                        )}
                      </div>
                    )}
                  </TableHead>
                ))}
              </TableRow>
            ))}
          </TableHeader>
          <TableBody>
            {isLoading ? (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  <div className="flex items-center justify-center">
                    <div className="animate-spin rounded-full h-6 w-6 border-b-2 border-primary"></div>
                    <span className="ml-2">Chargement des trades...</span>
                  </div>
                </TableCell>
              </TableRow>
            ) : table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() && 'selected'}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id}>
                      {flexRender(
                        cell.column.columnDef.cell,
                        cell.getContext()
                      )}
                    </TableCell>
                  ))}
                </TableRow>
              ))
            ) : (
              <TableRow>
                <TableCell colSpan={columns.length} className="h-24 text-center">
                  Aucun trade trouvé.
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between space-x-2 py-4">
        <div className="text-sm text-muted-foreground">
          Page {table.getState().pagination.pageIndex + 1} sur{' '}
          {table.getPageCount()} ({data.length} trades)
        </div>
        <div className="flex items-center space-x-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.previousPage()}
            disabled={!table.getCanPreviousPage()}
          >
            Précédent
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => table.nextPage()}
            disabled={!table.getCanNextPage()}
          >
            Suivant
          </Button>
          {hasMore && (
            <Button
              variant="outline"
              size="sm"
              onClick={onLoadMore}
              disabled={isLoading}
            >
              Charger plus
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};

export default TradesTable;

