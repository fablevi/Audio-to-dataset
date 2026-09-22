import os
import uuid
import logging
import pandas as pd
from pathlib import Path
from typing import List, Tuple, Callable, Dict, Any, Optional
from app.models.segment_record import SegmentRecord

logger = logging.getLogger(__name__)


class ParquetService:
    def __init__(self, output_dir: str = "/tmp/parquet_exports"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def _resolve_file_path(self, dataset_name: str) -> Path:
        """
        Ensures the dataset name has a .parquet extension and resolves its Path.
        """
        filename = dataset_name if dataset_name.endswith(".parquet") else f"{dataset_name}.parquet"
        return self.output_dir / filename

    def create_parquet(
        self, 
        records: List[SegmentRecord], 
        dataset_name: str = "dataset"
    ) -> Tuple[str, Callable[[], None]]:
        """
        Creates a new Parquet file with a unique ID suffix and returns file path with cleanup callback.
        """
        try:
            data = [record.model_dump() for record in records]
            df = pd.DataFrame(data)
            
            unique_id = uuid.uuid4().hex[:8]
            file_path = self.output_dir / f"{dataset_name}_{unique_id}.parquet"
            
            df.to_parquet(file_path, engine="pyarrow", index=False)
            logger.info(f"Parquet file created successfully at: {file_path}")

            def cleanup():
                try:
                    if file_path.exists():
                        file_path.unlink()
                        logger.info(f"Temporary Parquet file removed: {file_path}")
                except Exception as e:
                    logger.error(f"Failed to remove Parquet file '{file_path}': {e}")

            return str(file_path), cleanup

        except Exception as e:
            logger.error(f"Error while generating Parquet file: {str(e)}")
            raise

    def append_to_parquet(
        self, 
        dataset_name: str, 
        records: List[SegmentRecord]
    ) -> str:
        """
        Appends new SegmentRecords to an existing Parquet file by name.
        If the file does not exist, it creates a new one.
        """
        try:
            file_path = self._resolve_file_path(dataset_name)
            new_data = [record.model_dump() for record in records]
            new_df = pd.DataFrame(new_data)

            if file_path.exists():
                existing_df = pd.read_parquet(file_path, engine="pyarrow")
                combined_df = pd.concat([existing_df, new_df], ignore_index=True)
                logger.info(f"Appended {len(records)} records to existing file: {file_path.name}")
            else:
                combined_df = new_df
                logger.info(f"File not found. Created new Parquet file: {file_path.name}")

            combined_df.to_parquet(file_path, engine="pyarrow", index=False)
            return str(file_path)

        except Exception as e:
            logger.error(f"Failed to append records to Parquet file '{dataset_name}': {str(e)}")
            raise

    def list_parquet_files(self) -> List[Dict[str, Any]]:
        """
        Lists all available Parquet files in the storage directory with basic metadata.
        """
        files_info = []
        try:
            for file_path in self.output_dir.glob("*.parquet"):
                try:
                    df = pd.read_parquet(file_path, engine="pyarrow")
                    stat = file_path.stat()
                    files_info.append({
                        "filename": file_path.name,
                        "total_records": len(df),
                        "size_bytes": stat.st_size,
                        "last_modified": stat.st_mtime
                    })
                except Exception as file_err:
                    logger.warning(f"Could not read metadata for '{file_path.name}': {file_err}")

            return files_info

        except Exception as e:
            logger.error(f"Failed to list Parquet files: {str(e)}")
            raise

    def get_elements_slice(
        self, 
        dataset_name: str, 
        offset: int = 0, 
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Retrieves a slice of records from index 'offset' (x) up to 'offset + limit' (x + y).
        
        :param dataset_name: Name or filename of the Parquet dataset.
        :param offset: Starting row index (x).
        :param limit: Number of items to retrieve (y).
        :return: Dict containing records slice, total row count, offset, and limit.
        """
        try:
            file_path = self._resolve_file_path(dataset_name)

            if not file_path.exists():
                raise FileNotFoundError(f"Parquet dataset '{dataset_name}' does not exist.")

            df = pd.read_parquet(file_path, engine="pyarrow")
            total_records = len(df)

            # Slice DataFrame between x and x + y
            sliced_df = df.iloc[offset : offset + limit]
            
            # Replace NaN/None values appropriately for JSON serialization
            records = sliced_df.where(pd.notnull(sliced_df), None).to_dict(orient="records")

            logger.info(
                f"Retrieved {len(records)} records (offset: {offset}, limit: {limit}) "
                f"from '{file_path.name}' (total: {total_records})"
            )

            return {
                "dataset_name": file_path.name,
                "total_records": total_records,
                "offset": offset,
                "limit": limit,
                "records": records
            }

        except Exception as e:
            logger.error(f"Error reading slice from Parquet file '{dataset_name}': {str(e)}")
            raise